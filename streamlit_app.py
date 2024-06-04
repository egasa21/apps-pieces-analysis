import streamlit as st
from google_play_scraper import Sort, reviews as gps_reviews
from time import sleep
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import ssl

ssl._create_default_https_context = ssl._create_stdlib_context

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Function to scrape, process, and analyze reviews
def analyze_reviews(app_id, keywords_dict, lang='id', country='id', sort=Sort.NEWEST, filter_score_with=""):
    def scrape_reviews_batched(app_id, lang='id', country='id', sort=Sort.NEWEST, filter_score_with=""):
        all_reviews = []
        scraped_ids = set()
        for _ in range(9):  # Scrape 9 batches (adjust as needed)
            result, continuation_token = gps_reviews(app_id, lang=lang, country=country, sort=sort, count=100, filter_score_with=filter_score_with)
            all_reviews.extend(result)
            scraped_ids.update(review['reviewId'] for review in result)
            if not continuation_token:
                break  # No more pages to fetch, exit loop
            sleep(1)  # Delay for 1 second between batches
        return all_reviews
    
    reviews_data = scrape_reviews_batched(app_id, lang=lang, country=country, sort=sort, filter_score_with=filter_score_with)
    
    df = pd.DataFrame(reviews_data)
    
    # text cleaning
    def clean_text(text):
        text = text.lower()
        text = ''.join([char for char in text if char.isalnum() or char.isspace()])
        return text
    
    df['cleaned_review'] = df['content'].apply(clean_text)
    
    review_texts = df['cleaned_review'].tolist()
    
    # Extract values (keywords) from the dictionary
    keywords_list = list(keywords_dict.values())
    
    # Vectorize the keywords and reviews
    vectorizer = CountVectorizer().fit_transform(keywords_list + review_texts)
    keyword_vectors = vectorizer[:len(keywords_list)]
    review_vectors = vectorizer[len(keywords_list):]
    
    # Calculate cosine similarity between each review and each keyword
    similarities = cosine_similarity(keyword_vectors, review_vectors)
    
    # Set a threshold for cosine similarity
    threshold = 0.05
    
    # Initialize sentiment analyzer
    analyzer = SentimentIntensityAnalyzer()
    
    # Function to classify sentiment score into a scale of 1 to 5
    def classify_sentiment(score):
        if score <= -0.6:
            return 1
        elif score <= -0.2:
            return 2
        elif score < 0.2:
            return 3
        elif score < 0.6:
            return 4
        else:
            return 5
    
    # Filter reviews based on cosine similarity and categorize them by keyword
    keyword_to_reviews = {}
    
    for i, keyword in enumerate(keywords_list):
        relevant_reviews = [(review_texts[j], similarity) for j, similarity in enumerate(similarities[i]) if similarity > threshold]
        if relevant_reviews:
            keyword_to_reviews[keyword] = relevant_reviews
    
    # Prepare results for display
    results = []
    for keyword, review_list in keyword_to_reviews.items():
        sentiment_ratings = []
        keyword_result = {"keyword": keyword, "reviews": []}
        for review, score in review_list:
            sentiment_score = analyzer.polarity_scores(review)['compound']
            sentiment_rating = classify_sentiment(sentiment_score)
            sentiment_ratings.append(sentiment_rating)
            keyword_result["reviews"].append({"review": review, "score": score, "sentiment_rating": sentiment_rating})
        
        if sentiment_ratings:
            avg_sentiment = sum(sentiment_ratings) / len(sentiment_ratings)
            keyword_result["average_sentiment"] = avg_sentiment
        results.append(keyword_result)
    
    # Summarize overall sentiment
    overall_sentiment_ratings = []
    for review_list in keyword_to_reviews.values():
        for review, score in review_list:
            sentiment_score = analyzer.polarity_scores(review)['compound']
            sentiment_rating = classify_sentiment(sentiment_score)
            overall_sentiment_ratings.append(sentiment_rating)
    
    overall_avg_sentiment = None
    if overall_sentiment_ratings:
        overall_avg_sentiment = sum(overall_sentiment_ratings) / len(overall_sentiment_ratings)
    
    return results, overall_avg_sentiment

# Streamlit app
st.title("Google Play App Review Analysis")
app_id = st.text_input("Enter the app ID:", "id.or.muhammadiyah.quran")

keywords_dict = {0: "[('apakah max entertainment', 0.8594), ('layanan aplikasi hiburan', 0.8133), ('max entertainment', 0.796), ('aplikasi hiburan', 0.7845)]",
 1: "[('membuat pengguna yang mudah', 0.6543), ('pencarian aplikasi hiburan', 0.6436), ('fitur memudahkan', 0.6174), ('aplikasi hiburan', 0.6036)]",
 2: "[('aplikasi max entertainment', 0.7593), ('aplikasi mudah dioperasikan', 0.7565), ('operasi mudah', 0.7238), ('max entertainment', 0.7142)]",
 3: "[('layanan menyediakan whatsapp', 0.8746), ('memberikan whatsapp menurut', 0.8704), ('asalkan whatsapp', 0.8573), ('whatsapp menurut', 0.8195)]",
 4: "[('whatsapp menyediakan', 0.838), ('berikan pengguna kepuasan', 0.8278), ('memberikan kepuasan', 0.8037), ('pengguna kepuasan', 0.7675)]",
 5: "[('google classroom', 0.7231), ('tampilan antarmuka kelas', 0.594), ('antarmuka kelas', 0.5711), ('google', 0.5693)]",
 6: "[('fungsi google classroom', 0.8422), ('google classroom', 0.7956), ('gunakan google', 0.7742), ('google', 0.7092)]",
 7: "[('gunakan google classroom', 0.8085), ('google classroom', 0.7363), ('gunakan google', 0.6793), ('ruang kelas dengan mudah', 0.6131)]",
 8: "[('google classroom', 0.6268), ('kelas merespons pembatalan', 0.5667), ('google', 0.5238), ('tanggapan kelas', 0.5081)]",
 9: "[('menu ditampilkan google', 0.7691), ('ditampilkan google classroom', 0.7525), ('google classroom', 0.7169), ('ditampilkan google', 0.6366)]",
 10: "[('membantu pengguna baru', 0.7763), ('gunakan bantuan tutorial', 0.7671), ('bantuan tutorial', 0.739), ('tutorial penggunaan awal', 0.7376)]",
 11: "[('kelas google menurut', 0.8117), ('google classroom', 0.7998), ('informasi tersedia google', 0.779), ('tersedia google', 0.7354)]",
 12: "[('tampilkan google classroom', 0.7596), ('google classroom', 0.7039), ('tampilkan informasi google', 0.6338), ('kelas clear clear easy', 0.6291)]",
 13: "[('google classroom', 0.7077), ('kualitas layanan google', 0.7058), ('kelas google yang berkualitas', 0.6608), ('google berkualitas', 0.6107)]",
 14: "[('akses google classroom', 0.7054), ('google classroom', 0.6701), ('ruang kelas cukup murah', 0.618), ('akses data google', 0.605)]",
 15: "[('keamanan data', 0.7966), ('data pribadi pengguna', 0.7589), ('data pribadi', 0.7448), ('keamanan data dijamin', 0.7024)]",
 16: "[('formulir berisi google', 0.6048), ('membentuk kejahatan penipuan', 0.6022), ('google classroom', 0.5713), ('google classroom pertahankan', 0.5552)]",
 17: "[('google classroom make', 0.7348), ('google classroom', 0.7162), ('tidak menggunakan google', 0.6762), ('gunakan google', 0.6511)]",
 18: "[('kelas google classroom', 0.7937), ('google classroom', 0.7853), ('kelas pembelajaran yang membantu', 0.7047), ('ruang kelas membantu', 0.662)]",
 19: "[('kelas google menurut', 0.8389), ('google classroom', 0.819), ('layanan disediakan google', 0.8039), ('asalkan google', 0.7654)]",
 20: "[('google classroom', 0.7832), ('pengguna kepuasan kelas', 0.6717), ('google', 0.6509), ('kepuasan kelas', 0.6091)]",
 21: "[('dipelajari dengan mudah', 0.8817), ('panduan operasional dipelajari', 0.7227), ('panduan belajar', 0.7037), ('terpelajar', 0.6704)]",
 22: "[('digunakan dengan mudah', 0.9479), ('dengan mudah', 0.8683), ('program', 0.4656), ('program yang digunakan', 0.4651)]",
 23: "[('diakses dengan mudah', 0.795), ('dengan mudah', 0.6475), ('menu diakses', 0.5745), ('menu', 0.4943)]",
 24: "[('diakses dengan mudah', 0.9764), ('dengan mudah', 0.8737), ('informasi yang diakses', 0.5684), ('diakses', 0.5401)]",
 25: "[('menggunakan fitur filter', 0.797), ('item pencarian fitur', 0.7616), ('pencarian fitur', 0.749), ('menggunakan filter', 0.7345)]",
 26: "[('dilengkapi autocorrect autocorrect', 0.9158), ('dilengkapi autocorrect', 0.8915), ('koreksi otomatis koreksi otomatis', 0.8806), ('koreksi otomatis', 0.8524)]",
 27: "[('tutor teman', 0.7133), ('tutor', 0.6796), ('skenario membahas teman', 0.6679), ('skenario pembelajaran dibahas', 0.6182)]",
 28: "[('dosen tutor didorong', 0.7407), ('dosen tutor staf', 0.7347), ('tutor staf', 0.7034), ('dosen tutor', 0.6985)]",
 29: "[('fakultas memberi', 0.7693), ('proses pembelajaran independen', 0.7363), ('pembelajaran mandiri waktu', 0.7214), ('fakultas', 0.6971)]",
 30: "[('hasil pembelajaran penilaian', 0.7334), ('hasil belajar', 0.733), ('waktu mempersiapkan penilaian', 0.7076), ('pembelajaran penilaian', 0.6976)]",
 31: "[('proses pembelajaran hasil', 0.6413), ('dibawa mempersiapkan pembelajaran', 0.6386), ('siapkan proses pembelajaran', 0.6384), ('pembelajaran hasil', 0.6307)]",
 32: "[('skenario disampaikan tutorial', 0.8948), ('tutorial mendorong memahami', 0.8916), ('tutorial yang dikirimkan', 0.8686), ('tutorial mendorong', 0.8589)]",
 33: "[('ilmu kedokteran menjelaskan', 0.7407), ('menjelaskan masalah kesehatan', 0.672), ('ilmu kedokteran aplikasi', 0.6633), ('tutorial membantu memahami', 0.6464)]",
 34: "[('dosen guru', 0.8285), ('tutor dosen menyediakan', 0.8136), ('tutor memberikan umpan balik', 0.8069), ('tutor dosen', 0.788)]",
 35: "[('tutor dosen guru', 0.8151), ('tutor dosen menyediakan', 0.8011), ('dosen guru', 0.792), ('tutor dosen', 0.755)]",
 36: "[('berbagai ilmiah yang relevan', 0.8685), ('disiplin ilmiah', 0.8062), ('ilmiah yang relevan', 0.7967), ('ilmiah', 0.6991)]",
 37: "[('disiplin materi sains', 0.7585), ('sains disiplin hubungan', 0.7255), ('materi sains', 0.7044), ('sains disiplin', 0.6934)]",
 38: "[('disiplin ilmiah yang saling terkait', 0.7135), ('ujian akhir yang diuji', 0.6805), ('terdiri dari ilmiah yang saling terkait', 0.6725), ('ujian akhir terdiri', 0.6508)]",
 39: "[('disiplin materi pembelajaran', 0.7495), ('tes dilakukan', 0.7225), ('materi belajar', 0.7108), ('disiplin belajar', 0.699)]",
 40: "[('masalah kesehatan nyata', 0.6254), ('masalah kesehatan', 0.5732), ('belajar memfokuskan masalah', 0.5322), ('kesehatan', 0.5108)]",
 41: "[('komunitas masalah kesehatan', 0.6979), ('masalah kesehatan langsung', 0.5967), ('kesehatan', 0.5744), ('masalah kesehatan', 0.5602)]",
 42: "[('tindakan menangani kesehatan', 0.7401), ('masalah kesehatan', 0.6341), ('menangani kesehatan', 0.6167), ('kesehatan', 0.5738)]",
 43: "[('komunitas masalah kesehatan', 0.6945), ('kesehatan terkait', 0.634), ('masalah kesehatan terkait', 0.623), ('masalah kesehatan', 0.5771)]",
 44: "[('keterampilan menangani kesehatan', 0.7483), ('komunitas masalah kesehatan', 0.7319), ('menangani kesehatan', 0.6516), ('tes materi kuratif', 0.6416)]",
 45: "[('pilih materi pembelajaran', 0.7932), ('belajar materi yang diinginkan', 0.7823), ('belajar secara mendalam', 0.777), ('materi ingin belajar', 0.7666)]",
 46: "[('ingin hidup', 0.7017), ('mengusulkan pengajaran', 0.6513), ('mengusulkan metode pengajaran', 0.6476), ('metode mengajar menginginkan', 0.6259)]",
 47: "[('mengusulkan topik', 0.8363), ('material penting dinilai', 0.8311), ('topik materi', 0.8303), ('penting dinilai', 0.8004)]",
 48: "[('topik materi yang diuji', 0.9057), ('materi yang diuji sesuai', 0.8677), ('usulkan diuji', 0.8663), ('bahan accordance yang diuji', 0.8521)]",
 49: "[('diberikan sesuai dengan fakultas', 0.8393), ('pengalaman yang diberikan fakultas', 0.8348), ('kesesuaian fakultas', 0.783), ('tujuan pembelajaran disampaikan', 0.7793)]",
 50: "[('pengalaman yang diberikan fakultas', 0.7714), ('diberikan sesuai dengan fakultas', 0.7249), ('pengalaman belajar diberikan', 0.6785), ('praktisi umum', 0.6771)]",
 51: "[('proses belajar meningkat', 0.8945), ('proses meningkatkan pengetahuan', 0.8645), ('meningkatkan pengetahuan', 0.8176), ('pengetahuan secara bertahap', 0.8088)]",
 52: "[('kompleks mudah', 0.7094), ('diberikan secara bertahap sederhana', 0.7071), ('sedang belajar', 0.7009), ('kompleks mudah yang sederhana', 0.6955)]",
 53: "[('memulai patologis fisiologis', 0.8175), ('mulai fisiologis', 0.7167), ('materi yang diberikan secara bertahap', 0.6502), ('patologis fisiologis', 0.6268)]",
 54: "[('hasil pembelajaran penilaian', 0.9016), ('hasil belajar sesuai', 0.8955), ('pengalaman belajar yang diperoleh', 0.8935), ('hasil pembelajaran sesuai', 0.887)]",
 55: "[('tujuan pembelajaran diserahkan', 0.9355), ('sesuai dengan tujuan pembelajaran', 0.9277), ('hasil belajar sesuai', 0.9255), ('hasil pembelajaran sesuai', 0.9228)]",
 56: "[('teknik dengan mudah diakses', 0.8487), ('pengguna yang diakses dengan mudah', 0.8484), ('diakses dengan mudah', 0.7572), ('rekayasa mudah', 0.747)]",
 57: "[('waktu singkat mengalami', 0.5551), ('waktu yang relatif singkat', 0.5146), ('perintah nomor relatif', 0.5071), ('relatif pendek', 0.5013)]",
 58: "[('proses dengan cepat', 0.7027), ('dengan cepat', 0.5922), ('teknik merespons pembatalan', 0.5678), ('teknik informatika menanggapi', 0.5389)]",
 59: "[('informasi terus stabil', 0.711), ('lanjutkan stabil', 0.6815), ('informasi kinerja secara bersamaan', 0.6344), ('teknik digunakan secara bersamaan', 0.6257)]",
 60: "[('informasi dengan cepat', 0.7998), ('waktu yang dibutuhkan proses', 0.7471), ('total waktu yang dibutuhkan', 0.7218), ('waktu yang dibutuhkan', 0.7092)]",
 61: "[('informasi teknik disimpan', 0.7556), ('informasi yang disimpan sesuai', 0.7293), ('umm informatics engineering', 0.7256), ('informatika umm yang disimpan', 0.7173)]",
 62: "[('informasi pkn umm', 0.4925), ('informasi pkn', 0.4906), ('data store teknik', 0.4856), ('toko teknik', 0.4723)]",
 63: "[('data yang salah disimpan', 0.7218), ('data yang salah', 0.6771), ('mengandung kesalahan yang salah', 0.6711), ('kesalahan salah', 0.6588)]",
 64: "[('data duplikasi', 0.4702), ('pengurangan', 0.4669), ('pengurangan data duplikasi', 0.4647), ('data menyebabkan duplikasi', 0.4531)]",
 65: "[('sesuai diperlukan', 0.8956), ('diperlukan', 0.8214), ('kesesuaian informasi yang dihasilkan', 0.7363), ('kesesuaian informasi', 0.7345)]",
 66: "[('informasi pkn yang dihasilkan', 0.8131), ('informasi rekayasa informasi', 0.7918), ('format yang dihasilkan pkn', 0.7818), ('rekayasa informasi', 0.7636)]",
 67: "[('pengguna yang benar', 0.9373), ('digunakan dengan benar', 0.9355), ('berguna digunakan dengan benar', 0.9258), ('berguna digunakan', 0.8295)]",
 68: "[('informasi teknik informatika', 0.6987), ('informatika umm yang diproses', 0.6857), ('teknik informatika', 0.6785), ('umm informatics engineering', 0.6769)]",
 69: "[('informasi mudah dipelajari', 0.8371), ('mudah belajar mengerti', 0.8131), ('mudah belajar', 0.7594), ('informasi mudah', 0.7171)]",
 70: "[('informasi teknik informatika', 0.7726), ('informasi teknik mengandalkan', 0.7678), ('umm informatics engineering', 0.7527), ('informatika umm yang dihasilkan', 0.7423)]",
 71: "[('dapat mengurangi siswa', 0.6124), ('biaya siswa', 0.6084), ('praktik kerja', 0.5864), ('biaya siswa nyata', 0.5829)]",
 72: "[('informasi pkn yang lebih baik', 0.7073), ('proses pkn lebih baik', 0.6666), ('mengubah istilah pengembangan', 0.6539), ('istilah perubahan signifikan', 0.6268)]",
 73: "[('kejahatan penipuan', 0.7054), ('membentuk penipuan', 0.6382), ('berbagai bentuk penipuan', 0.6327), ('kejahatan', 0.5679)]",
 74: "[('kontrol terpusat', 0.9357), ('data kontrol', 0.8886), ('kontrol penggunaan data', 0.8806), ('terpusat', 0.8797)]",
 75: "[('informasi rekayasa bagus', 0.738), ('keamanan', 0.7097), ('umm keamanan', 0.6861), ('informasi teknik informatika', 0.676)]",
 76: "[('otorisasi menentukan akses', 0.79), ('memberikan penentuan otorisasi', 0.7667), ('penentuan otorisasi', 0.7456), ('gunakan operasi dengan jelas', 0.7447)]",
 77: "[('ketentuan waktu biaya', 0.7711), ('biaya ketentuan', 0.7306), ('mengurangi istilah pengguna', 0.7241), ('menggunakan pengguna yang meringankan', 0.7179)]",
 78: "[('proses universitas', 0.7255), ('peran informasi maju', 0.6792), ('universitas', 0.6602), ('informasi rekayasa informasi', 0.6397)]",
 79: "[('informatika praktik kerja', 0.7391), ('universitas teknik informatika', 0.7249), ('teknik informatika', 0.7194), ('sederhanakan proses nyata', 0.6995)]",
 80: "[('koordinator pkn menyediakan', 0.7456), ('koordinator memberikan bantuan', 0.7426), ('bantuan pengguna digunakan', 0.7081), ('koordinator menyediakan', 0.706)]",
 81: "[('mudah belajar mengerti', 0.8703), ('informasi rekayasa mudah', 0.8548), ('mudah belajar', 0.8222), ('informasi mudah', 0.7902)]",
 82: "[('informasi rekayasa mudah', 0.8822), ('penggunaan yang mudah', 0.8521), ('informasi mudah', 0.8458), ('mudah', 0.7713)]",
 83: "[('teknik berubah secara fleksibel', 0.8569), ('teknik berubah', 0.8085), ('umm informatics engineering', 0.7437), ('berubah secara fleksibel', 0.7415)]",
 84: "[('umm informatics engineering', 0.8814), ('teknik informatika', 0.8705), ('informasi rekayasa terkoordinasi', 0.8613), ('informasi terkoordinasi terintegrasi', 0.8309)]",
 85: "[('memberikan kepuasan siswa', 0.7388), ('pekerjaan siswa pkn', 0.7122), ('pekerjaan siswa', 0.7064), ('siswa kepuasan', 0.7053)]",
 86: "[('memenuhi kebutuhan pengguna', 0.816), ('situs web bertemu', 0.7642), ('bertemu pengguna', 0.7317), ('situs web', 0.6953)]",
 87: "[('memberikan pemuatan cepat', 0.7349), ('waktu pemuatan cepat', 0.7199), ('pemuatan cepat', 0.6844), ('situs web memberi', 0.5585)]",
 88: "[('format menu yang sesuai', 0.8276), ('menyajikan menu yang sesuai', 0.8144), ('menu sesuai', 0.7685), ('menu menu', 0.7174)]",
 89: "[('situs web menarik', 0.9422), ('penampilan yang menarik', 0.7525), ('menarik', 0.7037), ('situs web', 0.6371)]",
 90: "[('memudahkan beroperasi', 0.8564), ('operasi mudah', 0.8309), ('memudahkan', 0.7609), ('mudah', 0.7225)]",
 91: "[('surat mudah dimengerti', 0.7803), ('surat pengaturan mudah', 0.7387), ('surat pengaturan yang jelas', 0.7203), ('memberikan pengaturan yang jelas', 0.7035)]",
 92: "[('informasi yang akurat', 0.8059), ('informasi yang tepat akurat', 0.7757), ('memberikan akurat yang tepat', 0.7166), ('tepat', 0.7055)]",
 93: "[('situs web disajikan', 0.8145), ('disajikan menurut pengguna', 0.8117), ('sesuai kebutuhan pengguna', 0.7873), ('situs web', 0.7501)]",
 94: "[('persiapan yang benar', 0.9178), ('tata letak informasi persiapan', 0.8418), ('informasi persiapan', 0.7992), ('tata letak informasi', 0.7815)]",
 95: "[('situs web menyediakan sebelumnya', 0.7913), ('informasi sebelumnya terbaru', 0.7493), ('uptodate terbaru', 0.7419), ('informasi terbaru', 0.7163)]",
 96: "[('google chrome mozilla', 0.6764), ('firefox google', 0.651), ('chrome mozilla firefox', 0.6476), ('situs google chrome', 0.6414)]",
 97: "[('memudahkan persyaratan pengguna', 0.786), ('situs web kemudahan', 0.7775), ('memudahkan pengguna', 0.7127), ('kemudahan', 0.537)]",
 98: "[('situs web menyediakan', 0.8387), ('menyediakan pengguna akses', 0.7879), ('akses pengguna', 0.7633), ('situs web', 0.7606)]",
 99: "[('pengunggahan keamanan data', 0.8259), ('jaminan situs web', 0.8218), ('menjamin keamanan data', 0.8153), ('keamanan data', 0.7533)]",
 100: "[('menjamin pengunduhan keamanan', 0.9193), ('pengunduhan keamanan', 0.8742), ('jaminan situs web', 0.8206), ('menjamin keamanan', 0.7017)]",
 101: "[('panduan mudah dimengerti', 0.758), ('panduan arah mudah', 0.7473), ('panduan arah yang jelas', 0.7315), ('panduan mudah', 0.6855)]",
 102: "[('desain good easy', 0.6573), ('bagus mudah dimengerti', 0.6447), ('mudah dimengerti', 0.634), ('desain situs web', 0.6246)]",
 103: "[('menggunakan situs web yang dibuka', 0.663), ('menggunakan situs web', 0.6539), ('kesulitan menggunakan', 0.6034), ('situs web', 0.5853)]",
 104: "[('situs web', 0.3775), ('pengalaman', 0.3344), ('situs web mengalami gangguan', 0.3078), ('mengalami gangguan', 0.2749)]",
 105: "[('situs web diakses pc', 0.8857), ('pcs tablet mobile', 0.8754), ('tablet pcs', 0.8105), ('diakses pc', 0.7758)]",
 106: "[('opsi navigasi menu', 0.8057), ('opsi mudah dicari', 0.7534), ('navigasi menu', 0.7294), ('opsi mudah', 0.7239)]",
 107: "[('mudah digunakan interaktif', 0.7917), ('opsi navigasi mudah', 0.7739), ('opsi menu', 0.7556), ('navigasi mudah digunakan', 0.7443)]",
 108: "[('menu yang tersedia', 0.679), ('pembatalan menu yang tersedia', 0.6403), ('perintah mudah', 0.638), ('perintah pembatalan menu', 0.5767)]",
 109: "[('diperoleh dengan cepat', 0.9401), ('informasi dengan cepat', 0.9237), ('dengan cepat', 0.8177), ('diperoleh', 0.6692)]",
 110: "[('informasi yang cukup lengkap', 0.7457), ('informasi lengkap', 0.7164), ('cukup lengkap', 0.6451), ('menyelesaikan', 0.6296)]",
 111: "[('sesuai kebutuhan', 0.9221), ('fitur menurut', 0.8658), ('kebutuhan', 0.8613), ('fitur', 0.7996)]",
 112: "[('berbagai manfaat', 0.9332), ('promosi memberikan berbagai', 0.8731), ('manfaat', 0.8383), ('menyediakan promosi', 0.7722)]",
 113: "[('digunakan', 0.5163), ('kesalahan yang digunakan', 0.4284), ('kesalahan fitur digunakan', 0.4278), ('kesalahan', 0.4138)]",
 114: "[('menyaring kata kunci kata kunci', 0.9148), ('menyaring kata kunci', 0.8759), ('kata kunci kata kunci pencarian', 0.8557), ('pencarian kata kunci', 0.831)]",
 115: "[('yang ada', 0.641), ('pengguna', 0.6255), ('informasi', 0.5943), ('informasi yang ada diubah', 0.5568)]",
 116: "[('proses menyelesaikan makanan', 0.7802), ('menyelesaikan makanan', 0.7744), ('pembelian makanan', 0.767), ('makanan', 0.634)]",
 117: "[('hemat pembelian uang', 0.7701), ('membeli makanan', 0.7496), ('pembelian uang', 0.64), ('hemat', 0.6232)]",
 118: "[('waktu harga yang dipesan', 0.8096), ('hasilnya memesan harga', 0.8059), ('harga yang dipesan', 0.7632), ('hasil yang tepat dipesan', 0.7445)]",
 119: "[('makanan beli makanan', 0.8005), ('pesan pembelian makanan', 0.7669), ('memesan makanan', 0.7412), ('membeli makanan', 0.7398)]",
 120: "[('pengguna kepuasan', 0.9515), ('berikan pengguna kepuasan', 0.951), ('memberikan kepuasan', 0.9066), ('kepuasan', 0.8944)]",
 121: "[('aplikasi mudah diakses', 0.8028), ('pengguna yang mudah diakses', 0.7745), ('aplikasi dengan mudah', 0.7544), ('mudah diakses', 0.7115)]",
 122: "[('aplikasi video difasilitasi', 0.6175), ('seri soccer', 0.5913), ('aplikasi video', 0.5553), ('seri menonton yang difasilitasi', 0.5529)]",
 123: "[('menonton seri sepak bola', 0.8314), ('menonton sepak bola', 0.7818), ('aplikasi video berguna', 0.6893), ('aplikasi video', 0.6447)]",
 124: "[('aplikasi mudah belajar', 0.7425), ('pengguna belajar yang mudah', 0.7337), ('mudah belajar', 0.669), ('aplikasi mudah', 0.6473)]",
 125: "[('gunakan instruksi video', 0.914), ('aplikasi video', 0.8868), ('video instruksi', 0.8681), ('video', 0.7279)]",
 126: "[('pengguna yang mudah diakses', 0.8025), ('aplikasi mudah diakses', 0.8014), ('aplikasi dengan mudah', 0.7444), ('mudah diakses', 0.7414)]",
 127: "[('meminta pembatalan lebih cepat', 0.7225), ('aplikasi video menanggapi', 0.634), ('permintaan menanggapi lebih cepat', 0.5959), ('pembatalan lebih cepat', 0.5902)]",
 128: "[('akurasi tinggi', 0.7279), ('memberikan informasi tinggi', 0.685), ('aplikasi video menyediakan', 0.6786), ('aplikasi video', 0.631)]",
 129: "[('aplikasi video', 0.7128), ('pengguna suit informasi', 0.6476), ('sesuai dengan kebutuhan pengguna', 0.6067), ('kebutuhan pengguna', 0.5736)]",
 130: "[('aplikasi mendukung pembayaran', 0.804), ('aplikasi video', 0.761), ('mendukung aplikasi pembayaran', 0.7422), ('aplikasi pembayaran', 0.7265)]",
 131: "[('membandingkan teater jam tangan', 0.5972), ('menonton video seri', 0.5843), ('tonton bioskop', 0.5275), ('aplikasi video dibandingkan', 0.5037)]",
 132: "[('aplikasi video menarik', 0.653), ('menarik akses yang mencurigakan', 0.6056), ('aplikasi video', 0.5752), ('akses perangkat yang tidak diketahui', 0.5306)]",
 133: "[('standar aplikasi video', 0.8105), ('aplikasi video', 0.7464), ('keamanan data', 0.7394), ('standar data pribadi', 0.7236)]",
 134: "[('pemula yang digunakan', 0.7177), ('pemula', 0.7025), ('aplikasi video yang digunakan', 0.6965), ('aplikasi video', 0.6652)]",
 135: "[('pengguna dengan mudah bertanya', 0.646), ('fitur aplikasi video', 0.6232), ('acara aplikasi video', 0.6089), ('aplikasi video', 0.5523)]",
 136: "[('aplikasi video', 0.9531), ('video', 0.8716), ('aplikasi mengandalkan', 0.643), ('aplikasi', 0.6347)]",
 137: "[('aplikasi mudah dimengerti', 0.7862), ('penggunaan yang mudah dimengerti', 0.7494), ('aplikasi mudah', 0.7399), ('aplikasi video', 0.6962)]",
 138: "[('merasa video yang puas', 0.8726), ('video yang puas', 0.8403), ('aplikasi video disediakan', 0.6918), ('merasa puas', 0.6828)]",
 139: "[('layanan menyediakan video', 0.8288), ('video yang disediakan', 0.7973), ('aplikasi video', 0.7827), ('layanan berkualitas yang puas', 0.6861)]",
 140: "[('pengguna aplikasi video', 0.8392), ('aplikasi video aplikasi', 0.8172), ('video aplikasi video', 0.7873), ('rekomendasikan video', 0.7814)]",
 141: "[('lembaga dianggap cukup', 0.6702), ('lembaga yang berpartisipasi cepat', 0.6561), ('tujuan domestik nasional', 0.6502), ('domestik nasional', 0.6477)]",
 142: "[('waktu nyata secara instan', 0.6332), ('terjadi secara instan', 0.6126), ('transfer dana cepat', 0.5833), ('real instan', 0.5657)]",
 143: "[('pesanan transfer dana', 0.6508), ('tahap permintaan informasi', 0.6444), ('kueri informasi pelanggan', 0.638), ('proses transaksi terdiri', 0.6368)]",
 144: "[('penggunaan yang mudah', 0.7962), ('mudah mudah mudah', 0.7876), ('mudah mudah', 0.7555), ('bi cepat sederhana', 0.75)]",
 145: "[('hari hari', 0.5445), ('24 jam', 0.5367), ('berhenti 24 jam', 0.5303), ('365 hari tahun', 0.5298)]",
 146: "[('melebihi penyelesaian hari', 0.7453), ('melebihi hari', 0.7107), ('bi cepat melebihi', 0.6732), ('cepat melebihi', 0.6713)]",
 147: "[('validasi transfer dana', 0.7334), ('perintah mengirim transaksi', 0.7295), ('transfer perintah pengiriman', 0.7165), ('perintah transfer dana', 0.7131)]",
 148: "[('pengguna yang mudah diakses', 0.8676), ('aplikasi mudah diakses', 0.8639), ('mudah diakses', 0.7876), ('aplikasi dengan mudah', 0.7827)]",
 149: "[('lengkap dipasarkan', 0.9317), ('menyelesaikan', 0.82), ('produk yang dipasarkan', 0.6849), ('produk', 0.6702)]",
 150: "[('dibawa dengan cepat', 0.6022), ('aplikasi shopee merespons', 0.5602), ('aplikasi menanggapi pembatalan', 0.5115), ('dengan cepat', 0.5099)]",
 151: "[('konsumen lebih mudah dibuat', 0.7684), ('konsumen yang lebih mudah', 0.7212), ('menjadi lebih mudah', 0.593), ('lot memudahkan', 0.5868)]",
 152: "[('aplikasi disimpan menurut', 0.86), ('aplikasi tersimpan disimpan', 0.8353), ('aplikasi disimpan', 0.8206), ('aplikasi tersimpan', 0.819)]",
 153: "[('merilis informasi terbaru', 0.6347), ('shopee memberikan pemberitahuan', 0.611), ('informasi terakhir', 0.5668), ('memberikan pemberitahuan pemberitahuan', 0.563)]",
 154: "[('aplikasi shopee mengandalkan', 0.7989), ('informasi yang diproduksi shopee', 0.788), ('aplikasi shopee yang diproduksi', 0.7689), ('aplikasi shopee', 0.7352)]",
 155: "[('mudah belajar mengerti', 0.9), ('aplikasi yang disajikan mudah', 0.8969), ('mudah belajar', 0.8487), ('aplikasi mudah', 0.8465)]",
 156: "[('cukup murah', 0.7276), ('murah', 0.7084), ('aplikasi shopee cukup', 0.4882), ('akses shopee', 0.4286)]",
 157: "[('voucher', 0.692), ('diskon', 0.6626)]",
 158: "[('bebas biaya kirim', 0.7958), ('fasilitas meringankan pelanggan', 0.7896), ('meringankan pelanggan', 0.7821), ('fasilitas pengiriman meringankan', 0.6925)]",
 159: "[('data identitas pribadi', 0.8708), ('identitas pribadi konsumen', 0.827), ('data identitas', 0.7932), ('data dilindungi', 0.7281)]",
 160: "[('transaksi konsumen', 0.8394), ('data transaksi dilindungi', 0.8319), ('konsumen', 0.7261), ('data dilindungi', 0.726)]",
 161: "[('kartu kredit data', 0.7625), ('shopee memberikan perlindungan', 0.6847), ('shopee menyediakan', 0.6423), ('kredit data', 0.6055)]",
 162: "[('aplikasi mudah dimengerti', 0.8502), ('aplikasi mudah', 0.7688), ('mudah dimengerti', 0.6945), ('mudah', 0.6314)]",
 163: "[('informasi dengan cepat', 0.7611), ('waktu checkout pesanan', 0.649), ('produk waktu checkout', 0.6339), ('checkout pesanan', 0.6336)]",
 164: "[('halaman lama', 0.689), ('panjang halaman', 0.615), ('lama', 0.6062), ('panjang', 0.5506)]",
 165: "[('memfasilitasi penemuan konsumen', 0.8782), ('menemukan produk yang dibutuhkan', 0.8556), ('menemukan produk', 0.8375), ('konsumen menemukan', 0.8122)]",
 166: "[('cepat akurat', 0.921), ('layanan yang akurat', 0.897), ('tepat', 0.8222), ('cepat', 0.7192)]",
 167: "[('menerima kesalahan yang salah', 0.7741), ('salah rusak', 0.6707), ('rusak', 0.6461), ('menerima kesalahan', 0.6444)]",
 168: "[('membeli game shopee', 0.7301), ('pembelian produk shopee', 0.7125), ('shopee menyediakan', 0.6831), ('game shopee', 0.6807)]",
 169: "[('instruksi transaksi', 0.6496), ('memberikan transaksi instruksi', 0.6491), ('instruksi', 0.6449), ('instruksi transaksi diproses', 0.6146)]",
 170: "[('cepat akurat', 0.9351), ('layanan yang akurat', 0.886), ('tepat', 0.8351), ('cepat', 0.7737)]",
 171: "[('menerima kesalahan yang salah', 0.8109), ('salah rusak', 0.7328), ('menerima kesalahan', 0.7167), ('rusak', 0.689)]",
 172: "[('pengguna mulai produk', 0.6967), ('pembayaran tagihan hiburan', 0.6608), ('kredit pembelian produk', 0.6273), ('pembelian produk', 0.6141)]",
 173: "[('berikan instruksi', 0.6625), ('instruksi transaksi', 0.6513), ('memberikan transaksi instruksi', 0.6399), ('transaksi', 0.6338)]",
 174: "[('mytelkomsel dengan mudah', 0.9539), ('mudah diakses', 0.9376), ('dengan mudah', 0.8644), ('dapat diakses', 0.8022)]",
 175: "[('berfungsi secara optimal', 0.9183), ('secara optimal', 0.8099), ('fungsi', 0.6133), ('fungsi mytelkomsel', 0.5814)]",
 176: "[('memperoleh informasi dengan cepat', 0.9031), ('merespons dengan cepat diperoleh', 0.8597), ('menanggapi dengan cepat', 0.8178), ('dapatkan dengan cepat', 0.7952)]",
 177: "[('mytelkomsel menyediakan', 0.8958), ('memberikan informasi yang diperlukan', 0.8944), ('memberikan informasi', 0.8758), ('informasi yang dibutuhkan', 0.8658)]",
 178: "[('terlihat mudah dimengerti', 0.7987), ('informasi mytelkomsel dengan jelas', 0.7947), ('mudah terlihat mudah', 0.7827), ('informasi terlihat jelas', 0.7742)]",
 179: "[('data internet besar', 0.8377), ('internet besar', 0.7803), ('mytelkomsel membutuhkan besar', 0.775), ('kuota data internet', 0.7437)]",
 180: "[('paket mudah', 0.9219), ('mudah', 0.8183), ('kemasan', 0.5924), ('pembayaran paket', 0.5913)]",
 181: "[('berpengalaman', 0.4421), ('mytelkomsel', 0.4006), ('mytelkomsel berpengalaman', 0.3954), ('kesalahan', 0.3863)]",
 182: "[('aman menggunakan aplikasi', 0.8997), ('merasa aman menggunakan', 0.8421), ('merasa aman', 0.8081), ('menggunakan aman', 0.7861)]",
 183: "[('terorganisir efisien', 0.8954), ('pencarian terorganisir', 0.8297), ('efisien', 0.815), ('terorganisir', 0.7054)]",
 184: "[('data melihat yang bermanfaat', 0.8737), ('aplikasi tontonan bermanfaat', 0.8627), ('tontonan yang membantu', 0.8078), ('aplikasi kehadiran', 0.7959)]",
 185: "[('disediakan', 0.9494), ('diperlukan', 0.9058), ('pelayanan yang disediakan', 0.8894), ('jasa', 0.8285)]",
 186: "[('kepuasan pengguna', 0.9223), ('aplikasi memberi pengguna', 0.8216), ('memberi pengguna', 0.7818), ('kepuasan', 0.7795)]",
 187: "[('diakses dengan mudah', 0.6236), ('dengan mudah', 0.5014), ('informasi akte kelahiran', 0.4444), ('sertifikat hilang rusak', 0.4253)]",
 188: "[('diakses dengan mudah', 0.7453), ('dengan mudah', 0.6327), ('layanan pernikahan', 0.4751), ('pernikahan', 0.4749)]",
 189: "[('diakses dengan mudah', 0.5898), ('layanan kartu keluarga', 0.5252), ('kartu keluarga', 0.4814), ('dengan mudah', 0.457)]",
 190: "[('akta kelahiran', 0.5955), ('pengguna membutuhkan informasi', 0.5928), ('pengguna perlu', 0.5259), ('layanan sertifikat', 0.5047)]",
 191: "[('layanan pernikahan kk', 0.7172), ('pengguna membutuhkan informasi', 0.6244), ('pengguna kepuasan membutuhkan', 0.6235), ('pernikahan', 0.5919)]",
 192: "[('kartu keluarga', 0.6308), ('pengguna membutuhkan informasi', 0.5746), ('layanan kartu', 0.5685), ('layanan hilang rusak', 0.5032)]",
 193: "[('layanan akte kelahiran', 0.596), ('membantu pengguna kesulitan', 0.5748), ('kehilangan bantuan yang rusak', 0.5438)]",
 194: "[('pengguna sulit', 0.6231), ('layanan pernikahan kk', 0.5593), ('layanan layanan pernikahan', 0.5585), ('pernikahan layanan layanan', 0.5521)]",
 195: "[('membantu pengguna kesulitan', 0.6191), ('layanan hilang rusak', 0.6011), ('layanan kartu hilang', 0.5982), ('kehilangan bantuan yang rusak', 0.5948)]",
 196: "[('menyediakan pelanggan yang akurat', 0.8585), ('pelanggan yang akurat', 0.7909), ('pelayanan pelanggan', 0.7178), ('aplikasi shopee menyediakan', 0.7082)]",
 197: "[('aplikasi shopee', 0.7291), ('memesan fitur pembatalan', 0.7167), ('pembatalan pesanan yang efektif', 0.6225), ('shopee', 0.5953)]",
 198: "[('aplikasi shopee', 0.8961), ('aplikasi mengandalkan pengguna', 0.8221), ('shopee', 0.8004), ('pengguna', 0.7492)]",
 199: "[('cepat akurat', 0.921), ('layanan yang akurat', 0.897), ('tepat', 0.8222), ('cepat', 0.7192)]",
 200: "[('pengemudi yang bersangkutan pelanggan', 0.9069), ('keamanan pelanggan', 0.8437), ('pelanggan yang prihatin', 0.8071), ('pengemudi prihatin', 0.793)]",
 201: "[('waktu pengemudi', 0.8271), ('memilih waktu', 0.7994), ('pengemudi', 0.7383), ('pemetikan', 0.6987)]",
 202: "[('jenis layanan', 0.9229), ('layanan menurut ditawarkan', 0.8676), ('tipe', 0.8652), ('layanan menurut', 0.8597)]",
 203: "[('aplikasi menu', 0.8938), ('penggunaan aplikasi menu', 0.8929), ('menu panduan', 0.8887), ('menu', 0.7966)]",
 204: "[('pencarian informasi', 0.9273), ('fitur informasi yang digunakan', 0.8752), ('fitur yang digunakan', 0.8159), ('informasi', 0.7957)]",
 205: "[('menu ekraf ukm', 0.8888), ('ekraf ukm', 0.849), ('menu pendaftaran', 0.8262), ('menu ekraf', 0.8145)]",
 206: "[('kritik menu saran', 0.9339), ('kritik menu', 0.9025), ('pengguna kritik', 0.7766), ('menu saran', 0.7704)]",
 207: "[('perlu meningkatkan kinerja', 0.751), ('perlu informasi meningkat', 0.7461), ('meningkatkan kinerja', 0.7178), ('memberikan pertemuan kepuasan', 0.7137)]",
 208: "[('aplikasi daytrans', 0.6097), ('informasi diperbarui diperbarui', 0.6088), ('diperbarui diperbarui', 0.6025), ('memberikan informasi yang diperbarui', 0.5737)]",
 209: "[('layanan ditawarkan daytrans', 0.8877), ('aplikasi daytrans diharapkan', 0.8646), ('ditawarkan daytrans', 0.8294), ('aplikasi daytrans', 0.814)]",
 210: "[('fleksibel digunakan baru', 0.812), ('situasi baru', 0.7632), ('digunakan baru', 0.7259), ('informasi daytrans fleksibel', 0.7174)]",
 211: "[('aplikasi yang dibutuhkan', 0.945), ('layanan menyediakan aplikasi', 0.8797), ('aplikasi yang disediakan', 0.8306), ('pelayanan yang disediakan', 0.8275)]",
 212: "[('disediakan', 0.9295), ('diperlukan', 0.8952), ('informasi yang diberikan', 0.7929), ('informasi', 0.7332)]",
 213: "[('cepat akurat', 0.921), ('layanan yang akurat', 0.897), ('tepat', 0.8222), ('cepat', 0.7192)]",
 214: "[('ovo senang berikan', 0.7068), ('ovo senang', 0.6721), ('senang menyediakan jalan', 0.6718), ('berikan senang', 0.6548)]",
 215: "[('aplikasi memberi tahu pengguna', 0.8483), ('memberitahu layanan pengguna', 0.8022), ('aplikasi ovo', 0.7731), ('layanan pengguna digunakan', 0.7668)]",
 216: "[('aplikasi memberikan bantuan', 0.518), ('aplikasi ovo', 0.5149), ('memberikan bantuan terkait', 0.5036), ('aplikasi menyediakan', 0.4859)]",
 217: "[('aplikasi ovo memberi', 0.7298), ('aplikasi memberi individu', 0.7105), ('pengguna perhatian', 0.6865), ('pengguna', 0.6847)]",
 218: "[('ovo menerima', 0.5596), ('menerima saran', 0.5192), ('menerima kritik saran', 0.4986), ('pengguna', 0.3983)]",
 219: "[('gunakan transaksi berulang', 0.7419), ('aplikasi ovo nyaman', 0.6943), ('transaksi berulang', 0.6765), ('aplikasi penggunaan yang nyaman', 0.6478)]",
 220: "[('mudah belajar mengerti', 0.8703), ('informasi rekayasa mudah', 0.8548), ('mudah belajar', 0.8222), ('informasi mudah', 0.7902)]",
 221: "[('informasi rekayasa mudah', 0.8822), ('penggunaan yang mudah', 0.8521), ('informasi mudah', 0.8458), ('mudah', 0.7713)]",
 222: "[('umm berubah secara fleksibel', 0.7793), ('berubah secara fleksibel', 0.7457), ('umm rekayasa informatika', 0.7234), ('rekayasa informatika informasi', 0.71)]",
 223: "[('umm informatics engineering', 0.8814), ('teknik informatika', 0.8705), ('informasi rekayasa terkoordinasi', 0.8613), ('informasi terkoordinasi terintegrasi', 0.8309)]",
 224: "[('memberikan kepuasan siswa', 0.7388), ('pekerjaan siswa pkn', 0.7122), ('pekerjaan siswa', 0.7064), ('siswa kepuasan', 0.7053)]",
 225: "[('pajak pelaporan informasi', 0.5829), ('pelaporan pajak spt', 0.5728), ('pajak pelaporan', 0.5364), ('informasi dgt online', 0.5046)]",
 226: "[('pajak pelaporan online', 0.7742), ('pajak penggunaan mudah', 0.7405), ('pajak mudah', 0.6717), ('melaporkan pajak', 0.6305)]",
 227: "[('informasi dgt online', 0.6542), ('pelaporan online', 0.6519), ('spt pelaporan online', 0.6519), ('pajak fleksibel spt', 0.6419)]",
 228: "[('pelaporan pajak berubah', 0.8172), ('pajak pelaporan online', 0.793), ('pajak berubah', 0.7631), ('melaporkan pajak', 0.6537)]",
 229: "[('pajak spt terkoordinasi', 0.7972), ('pelaporan pajak spt', 0.778), ('informasi pelaporan online', 0.7266), ('pajak pelaporan', 0.7243)]",
 230: "[('pajak spt menyediakan', 0.741), ('pajak memberikan', 0.6923), ('pajak spt', 0.6791), ('pajak memberikan kepuasan', 0.6689)]"}


if st.button("Analyze Reviews"):
    with st.spinner("Analyzing reviews..."):
        results, overall_avg_sentiment = analyze_reviews(app_id, keywords_dict)

    if results:
        st.header("Analysis Results")
        # table_data = []
        # for result in results:
        #     for review in result["reviews"]:
        #         table_data.append({
        #             "Keyword": result["keyword"],
        #             "Review": review["review"],
        #             "Score": review["score"],
        #             "Sentiment Rating": review["sentiment_rating"]
        #         })
        
        st.write(f"Services Domain Score: {overall_avg_sentiment:.2f}") #Average Score
        # st.table(pd.DataFrame(table_data).set_index("Keyword").reset_index())