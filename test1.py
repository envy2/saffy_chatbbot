# -*- coding: utf-8 -*-
import json
import requests
import re
import urllib.request


from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = 'xoxb-506062083639-507668325765-cZ4SrQPnQMFrAEeBfXHIcSNE'
slack_client_id = '506062083639.507297033060'
slack_client_secret = '861513b13cd9ffd31df16e11a2cddc91'
slack_verification = 'vSRyDdNFD9tmfNBGP0Za6CMZ'
sc = SlackClient(slack_token)


# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    # 여기에 함수를 구현해봅시다.
    word = text.split(' ')
    url = 'https://terms.naver.com/search.nhn?query='+ word[1]
    url2 = 'https://endic.naver.com/search.nhn?sLn=kr&isOnlyViewEE=N&query=' + word[1]

    req = requests.get(url)
    req.encoding = 'utf-8'
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')

    words = []
    a = re.compile('[a-zA-Z]+')

    if (a.match(word[1]) != None):
        sourcecode1 = urllib.request.urlopen(url2).read()
        soupZ = BeautifulSoup(sourcecode1, 'html.parser')

        words.append("영어사전: " +soupZ.find("span", class_="fnt_k09").get_text() + soupZ.find("span", class_="fnt_k05").get_text()+'\n')


    if soup.find("strong", class_="keyword").get_text() == word[1]:
        words.append("요약: "+soup.find("span", class_="desc").get_text())

    for i, dict in enumerate(soup.find_all('strong', class_="title")):
        if (3 < i < 6):
            know_dict = "https://terms.naver.com" + dict.find("a")["href"]
            sourcecode = urllib.request.urlopen(know_dict).read()
            soup1 = BeautifulSoup(sourcecode, "html.parser")

            words.append("<출처> "+soup1.find("p", class_="cite").get_text())
            words.append("검색어: "+soup1.find("h2", class_="headword").get_text())
            words.append("의미: "+soup1.find("p", class_="txt").get_text()+"\n")


    return (u'\n'.join(words))

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
