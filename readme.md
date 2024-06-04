If this is your first time setting up this repo:

**Google Play App Review Analysis**

**Getting Started**

To get started with this project, you'll need to set up a virtual environment and install the necessary libraries. Here are the steps:

1. Install the virtual environment:
```
python3 -m venv venv
```
2. Activate the virtual environment:
```
source ./venv/bin/activate
```
3. Install the required libraries:
```
pip install streamlit google-play-scraper nltk scikit-learn vaderSentiment
```

**Running the Project**

Once you have installed all the necessary libraries, you can run the project by executing the following command:
```
streamlit run app.py
```
This will start the Streamlit app, and you can access it by navigating to `http://localhost:8501` in your web browser.

**Usage**

To use the app, simply enter the app ID of the Google Play app you want to analyze, and click the "Analyze Reviews" button. The app will then scrape and analyze the reviews for that app, and display the results in a table.

**Note**

Make sure to replace `app_id` with the actual ID of the Google Play app you want to analyze.

**License**

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

**Authors**

* [Ega Saputra]

I hope this helps! Let me know if you have any questions or need further assistance.