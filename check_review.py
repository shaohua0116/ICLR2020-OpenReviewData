from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import string
import sys
executable_path = '/usr/local/bin/chromedriver'
options = Options()
options.add_argument("--headless")
browser = webdriver.Chrome(options=options, executable_path=executable_path)

# Usage: python check_review.py URL YOUR_EMAIL YOUR_SENDER_EMAIL YOUR_SENDER_PASSWORD
sender_name = 'Shao-Hua Sun'
url = sys.argv[1]
receiver_email = sys.argv[2]
sender_email = sys.argv[3]
sender_password = sys.argv[4]

print("Monitor {} for {}".format(url, receiver_email))

def send_email(sender_name, sender_email, sender_password, receiver_email, title, info):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    body = "        <html>\n"+\
        "        <head></head>\n"+\
        "            <body>\n"+\
        "            <p>\n"+\
        "                The reviews or the ratings of your paper ({}) has changed: <br>{}.<br>\n".format(title, info)+\
        "            </p>\n"+\
        "            </body>\n"+\
        "        </html>\n"

    fromaddr = sender_password
    msg = MIMEMultipart()
    msg['From'] = sender_name
    msg['To'] = receiver_email
    msg['Subject'] = "Openreview Notification"

    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(fromaddr, receiver_email, text)
    server.quit()

def diff_review_rating(old_review, old_rating, review, rating):
    if old_rating is None or old_rating is None:
        return False, ""
    if not old_review == review:
        return True, "The review len (# of chars) has changed from {} to {}".format(
            [len(r) for r in old_review], [len(r) for r in review])
    if not old_rating == rating:
        return True, "The score has changed from {} to {}".format(old_rating, rating)
    return False, ""

old_review = None
old_rating = None
while True:
    browser.get(url)
    sleep(1)

    key = browser.find_elements_by_class_name("note_content_field")
    key = [k.text for k in key]
    withdrawn = 'Withdrawal Confirmation:' in key
    desk_reject = 'Desk Reject Comments:' in key
    value = browser.find_elements_by_class_name("note_content_value")
    value = [v.text for v in value]

    # title
    title = string.capwords(browser.find_element_by_class_name("note_content_title").text)
    # abstract
    valid = False
    tries = 0
    while not valid:
        if 'Abstract:' in key:
            valid = True
        else:
            time.sleep(wait_time)
            tries += 1
            key = browser.find_elements_by_class_name("note_content_field")
            key = [k.text for k in key]
            withdrawn = 'Withdrawal Confirmation:' in key
            desk_reject = 'Desk Reject Comments:' in key
            value = browser.find_elements_by_class_name("note_content_value")
            value = [v.text for v in value]
            if tries >= max_try:
                print('Reached max try: {} ({})'.format(title, url))
                break
    abstract = ' '.join(value[key.index('Abstract:')].split('\n'))

    # rating
    rating_idx = [i for i, x in enumerate(key) if x == "Rating:"]
    rating = []
    if len(rating_idx) > 0:
        for idx in rating_idx:
            rating.append(int(value[idx].split(":")[0]))

    review_idx = [i for i, x in enumerate(key) if x == "Review:"]
    review = []
    review_len = []
    if len(review_idx) > 0:
        for idx in review_idx:
            review_len.append(len([w for w in value[idx].replace('\n', ' ').split(' ') if not w == '']))
            review.append(value[idx])

    diff, info = diff_review_rating(old_review, old_rating, review, rating)
    if diff:
        print(info)
        send_email(sender_name, sender_email, sender_password, receiver_email, title, info)

    old_review = review
    old_rating = rating

    print('The review len: {}, rating: {}'.format(review_len, rating))
    sleep(600)
