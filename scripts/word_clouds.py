import markdown
from bs4 import BeautifulSoup
from wordcloud import WordCloud


def get_topics_word_cloud():
    with open("./topics.md", "r", encoding="utf-8") as input_file:
        text = input_file.read()
    html = markdown.markdown(text)
    soup = BeautifulSoup(html, 'html.parser')
    topics = [topic.text for topic in soup.find("ul").findAll("a")]
    entries = [len(list.findAll("li")) for list in soup.findAll("ul")[1:]]
    data = {t: e for t, e in zip(topics, entries)}
    wc = WordCloud(background_color=None, max_words=1000, width=800, height=500, 
                scale=4, mode="RGBA", relative_scaling=0, colormap="jet",
                contour_color="white")
    # generate word cloud
    wc.generate_from_frequencies(data)
    wc.to_file("./assets/wordcloud_by_topic.png")

def get_languages_word_cloud():
    with open("./languages.md", "r", encoding="utf-8") as input_file:
        text = input_file.read()
    html = markdown.markdown(text)
    soup = BeautifulSoup(html, 'html.parser')
    topics = [topic.text for topic in soup.find("ul").findAll("a")]
    entries = [len(list.findAll("li")) for list in soup.findAll("ul")[1:]]
    data = {t: e for t, e in zip(topics, entries)}
    wc = WordCloud(background_color=None, max_words=1000, width=800, height=500, 
                scale=4, mode="RGBA", relative_scaling=0, colormap="jet",
                contour_color="white")
    wc.generate_from_frequencies(data)
    wc.to_file("./assets/wordcloud_by_language.png")

if __name__ == "__main__":
    get_topics_word_cloud()
    get_languages_word_cloud()

