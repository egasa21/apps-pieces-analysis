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

from keywords import keywords_dict

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