import os
import re
import time
import json
import html
import math
import codecs
import random
import pandas as pd
import numpy as np
from textblob import TextBlob
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by  import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support    import expected_conditions

def save_as(filename, df, sep, end):
    with open(filename, 'a') as f:
        myCsv = df.astype(str).apply(lambda x: sep.join(x) + end, axis=1)
        myCsv.rename(sep.join(df.columns)).to_csv(f, mode='a', index=False, header=f.tell()==0)

def remove_excess_space(text):
    return ' '.join([x.strip() for x in text.split(' ') if x.strip() != ''])

def pretty_print(jsondata):
    print(json.dumps(jsondata, indent=4)) 

def remove_html_tags(text):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)

def get_sentiments(textblob):
    polarities = []
    subjectivities = []
    if len(textblob) == 0:
        return (np.nan, np.nan)
    for sentence in textblob.sentences:
        polarities.append(sentence.sentiment.polarity)
        subjectivities.append(sentence.sentiment.subjectivity)
    return (sum(polarities)/len(polarities), sum(subjectivities)/len(subjectivities)) 

def get_project_json(webpage):
    project_json_regex = r"window\.current_project = \"(.*?)\""
    match = re.search(project_json_regex, webpage).group(1) 
    proj_obj = codecs.decode(html.unescape(match), 'unicode_escape')
    return json.loads(proj_obj)

def get_json_from_api(browser, apiurl):
    browser.get(apiurl)
    browser.refresh()
    jsonEl = WebDriverWait(browser,5).until(lambda d: d.find_element_by_id("json"))
    pre = jsonEl.text
    return json.loads(pre)

def get_urls(choice):
    url_list = []
    url_path = "/Users/cheenu/Desktop/Kickstarter Scraper/kickstarterUrls_remaining.txt"
    with open(url_path,"r") as urls:
        url_list = urls.read().split(',')
    return url_list

options = Options()
options.add_argument("--headless")
firefox_capabilities = webdriver.DesiredCapabilities.FIREFOX
firefox_capabilities['marionette'] = True
browser = webdriver.Firefox(options=options, capabilities=firefox_capabilities)
browser.set_window_size(1366, 768)
while True:
    print("Attempting...")
    try:
        while True:
            start = time.time()
            urls = get_urls('y')
            current_url = urls[0]
            browser.get(current_url)
            print(current_url)
            html_text = browser.page_source
            project_json = get_project_json(html_text)
            projects_dict = {
                "project_id":[],
                "content_text":[],
                "risk_text":[],
                "pledge_per_backer":[],
                "content_images":[],
                "content_videos":[],
                "content_words":[],
                "content_length":[],
                "content_polarity":[],
                "content_subjectivity":[],
                "risk_words":[],
                "risk_length":[],
                "risk_polarity":[],
                "risk_subjectivity":[],
                "comments_count":[],
                "updates_count":[],
                "rewards_count":[],
                "total_min_reward":[],
                "min_reward_wt_avg":[],
                "backer_belief":[],
            }
            project_id = project_json["id"]
            print(project_id)
            projects_dict["project_id"].append(project_id)
            total_pledged = float(project_json["converted_pledged_amount"])
            backers_count = project_json["backers_count"]
            pledge_per_backer = total_pledged/backers_count if backers_count > 0 else 0.0
            projects_dict["pledge_per_backer"].append(pledge_per_backer)
            wait = WebDriverWait(browser,3)
            wait.until(expected_conditions.presence_of_element_located((By.CLASS_NAME, "rte__content")))
            project_description = browser.find_element_by_xpath('//div[@class="rte__content"]').get_attribute("innerHTML")
            risk_description = browser.find_element_by_xpath('//p[@class="js-risks-text text-preline"]').get_attribute("innerHTML")
            soup = BeautifulSoup(project_description, "html.parser")
            projects_dict["content_images"].append(len(soup.find_all("figure")))
            projects_dict["content_videos"].append(len(soup.find_all("div", {"class": "clip"})))
            content_desc = soup.find_all(['h1','h2','h3','h4','h5','h6','p'])
            desc_parsed = ''.join([str(x) for x in content_desc])
            desc_parsed = remove_excess_space(remove_html_tags(desc_parsed))
            space_removed_desc = TextBlob(desc_parsed)
            projects_dict['content_text'].append(space_removed_desc)
            projects_dict["content_words"].append(len(space_removed_desc.words))
            projects_dict["content_length"].append(len(space_removed_desc))
            content_sentiments = get_sentiments(space_removed_desc)
            projects_dict["content_polarity"].append(content_sentiments[0])
            projects_dict["content_subjectivity"].append(content_sentiments[1])
            risk_parsed = ''.join([str(x) for x in risk_description])
            risk_parsed = remove_excess_space(risk_parsed)
            space_removed_risk = TextBlob(risk_parsed)
            projects_dict['risk_text'].append(space_removed_risk)
            projects_dict["risk_words"].append(len(space_removed_risk.words))
            projects_dict["risk_length"].append(len(space_removed_risk))
            risk_sentiments = get_sentiments(space_removed_risk)
            projects_dict["risk_polarity"].append(risk_sentiments[0])
            projects_dict["risk_subjectivity"].append(risk_sentiments[1])
            projects_dict["comments_count"].append(project_json["comments_count"])
            updates_count = project_json["updates_count"]
            projects_dict["updates_count"].append(updates_count)
            rewards = project_json["rewards"]
            reward_count = len(rewards)-1
            projects_dict["rewards_count"].append(reward_count)
            reward_dict = {
                "reward_id":[],
                "project_id":[],
                "reward_title":[],
                "reward_desc":[],
                "reward_title_length":[],
                "reward_title_words":[],
                "reward_desc_length":[],
                "reward_desc_words":[],
                "reward_desc_polarity":[],
                "reward_desc_subjectivity":[],
                "reward_minimum":[],
                "reward_limit":[],
                "estimated_delivery":[],
                "reward_shipping":[],
                "reward_backers":[]
            }
            for reward in rewards:
                if reward['description'] == "No Reward":
                    continue
                reward_title = TextBlob(reward["title"])
                reward_desc = TextBlob(reward["description"])
                reward_dict["reward_id"].append(reward["id"])
                reward_dict["project_id"].append(project_id)
                reward_dict["reward_title"].append(reward_title)
                reward_dict["reward_desc"].append(reward_desc)
                reward_dict["reward_title_length"].append(len(reward["title"]))
                reward_dict["reward_title_words"].append(len(reward_title.words))
                reward_dict["reward_desc_length"].append(len(reward["description"]))
                reward_dict["reward_desc_words"].append(len(reward_desc.words))
                reward_desc_sentiments = get_sentiments(reward_desc)
                reward_dict["reward_desc_polarity"].append(reward_desc_sentiments[0])
                reward_dict["reward_desc_subjectivity"].append(reward_desc_sentiments[1])
                reward_dict["reward_minimum"].append(reward["converted_minimum"])
                reward_dict["reward_backers"].append(reward["backers_count"])
                reward_dict["estimated_delivery"].append(pd.to_datetime(reward["estimated_delivery_on"], unit='s'))
                reward_dict["reward_shipping"].append(reward["shipping_type"])
                reward_dict["reward_limit"].append(0 if 'limit' not in reward else reward['limit'])
            rewards_df = pd.DataFrame(reward_dict)
            rewards_df['tier_total'] = rewards_df.reward_minimum * rewards_df.reward_backers
            rewards_df['tier_contribution'] = rewards_df.reward_minimum / total_pledged
            rewards_df['tier_weighted_total'] = rewards_df['tier_total'] * rewards_df['tier_contribution']
            print("Processed rewards for project %d in %.3f seconds." %(project_id ,time.time() - start))
            total_reward_sum = rewards_df.sum()
            projects_dict["total_min_reward"].append(total_reward_sum['tier_total'])
            projects_dict["min_reward_wt_avg"].append(total_reward_sum['tier_weighted_total']/total_reward_sum['tier_contribution'])
            expected_pledged_with_reward = pledge_per_backer * total_reward_sum['reward_backers']
            extra_pledged = total_pledged - expected_pledged_with_reward
            projects_dict["backer_belief"].append(1 - (extra_pledged / total_pledged) if total_pledged > 0.0 else 0.0)
            projects_df = pd.DataFrame(projects_dict)
            print("Processed info for project %d in %.3f seconds." %(project_id ,time.time() - start))
            updates_api = project_json["urls"]["api"]["updates"]
            project_updates_json = get_json_from_api(browser, updates_api)
            author_api = project_json["creator"]["urls"]["api"]["user"]
            project_author_json = get_json_from_api(browser, author_api)
            api_retrieval_count = math.ceil(updates_count / 10) 
            updates_dict = {
                "post_id":[],
                "project_id":[],
                "post_title":[],
                "post_body":[],
                "title_length":[],
                "title_words":[],
                "title_polarity":[],
                "title_subjectivity":[],
                "body_visible":[],
                "body_length":[],
                "body_words":[],
                "body_polarity":[],
                "body_subjectivity":[],
                "body_images":[],
                "body_links":[],
                "published_at":[],
                "comments_count":[],
                "likes_count":[]
            }
            for i in range(api_retrieval_count):
                next_page_api = project_updates_json["urls"]["api"]["more_updates"]
                for update in project_updates_json["updates"]:
                    updates_dict["post_id"].append(update["id"])
                    updates_dict["project_id"].append(project_id)
                    updates_dict["published_at"].append(pd.to_datetime(update["published_at"], unit='s'))
                    title = TextBlob(update["title"])
                    updates_dict["post_title"].append(title)
                    updates_dict["title_length"].append(len(title))
                    updates_dict["title_words"].append(len(title.words))
                    title_sentiments = get_sentiments(title)
                    updates_dict["title_polarity"].append(title_sentiments[0])
                    updates_dict["title_subjectivity"].append(title_sentiments[1])
                    updates_dict["body_visible"].append(0 if update["visible"] == 'false' else 1)
                    if "body" in update:
                        body_text = update["body"]
                        body_soup = BeautifulSoup(body_text, "lxml")
                        body_links = body_soup.find_all("a")
                        updates_dict["body_links"].append(len(body_links))
                        body_images = body_soup.find_all("div", {"class": "template asset"})
                        updates_dict["body_images"].append(len(body_images))
                        body_desc = body_soup.find_all(['h1','h2','h3','h4','h5','h6','p'])
                        body_parsed = ''.join([str(x) for x in body_desc])
                        body_parsed = remove_excess_space(remove_html_tags(body_parsed))
                        space_removed_body = TextBlob(body_parsed)
                        updates_dict["post_body"].append(space_removed_body)
                        updates_dict["body_length"].append(len(space_removed_body))
                        updates_dict["body_words"].append(len(space_removed_body.words))
                        body_sentiments = get_sentiments(space_removed_body)
                        updates_dict["body_polarity"].append(body_sentiments[0])
                        updates_dict["body_subjectivity"].append(body_sentiments[1])
                    else:
                        updates_dict["post_body"].append('')
                        updates_dict["body_links"].append(np.nan)
                        updates_dict["body_images"].append(np.nan)
                        updates_dict["body_length"].append(np.nan)
                        updates_dict["body_words"].append(np.nan)
                        updates_dict["body_polarity"].append(np.nan)
                        updates_dict["body_subjectivity"].append(np.nan)
                    updates_dict["comments_count"].append(update["comments_count"])
                    updates_dict["likes_count"].append(update["likes_count"])
                project_updates_json = get_json_from_api(browser, next_page_api)
            updates_df = pd.DataFrame(updates_dict)
            print("Processed updates for project %d in %.3f seconds." %(project_id ,time.time() - start))
            authors_dict = {
                "author_id":[],
                "project_id":[],
                "author_name":[],
                "author_bio":[],
                "bio_length":[],
                "bio_words":[],
                "bio_polarity":[],
                "bio_subjectivity":[],
                "author_created":[],
                "author_backed":[],
                "author_join_year":[]
            }
            authors_dict["project_id"].append(project_id)
            authors_dict["author_id"].append(project_json["creator"]["id"])
            authors_dict["author_name"].append(project_json["creator"]["name"])
            authors_dict["author_backed"].append(project_author_json["backed_projects_count"])
            authors_dict["author_created"].append(project_author_json["created_projects_count"])
            author_bio = remove_excess_space(project_author_json["biography"])
            space_removed_bio = TextBlob(author_bio)
            authors_dict["author_bio"].append(author_bio)
            authors_dict["bio_length"].append(len(space_removed_bio))
            authors_dict["bio_words"].append(len(space_removed_bio.words))
            author_bio_sentiments = get_sentiments(space_removed_bio)
            authors_dict["bio_polarity"].append(author_bio_sentiments[0])
            authors_dict["bio_subjectivity"].append(author_bio_sentiments[1])
            authors_dict["author_join_year"].append(int(project_author_json["join_date"].split('-')[0]))
            authors_df = pd.DataFrame(authors_dict)
            print("Processed author info for project %d in %.3f seconds.\n" %(project_id ,time.time() - start))
            if not projects_df.empty and not rewards_df.empty and not authors_df.empty:
                save_as("./output/projects_text.txt",projects_df,sep=":::",end="|||")
                save_as("./output/rewards_text.txt",rewards_df,sep=":::",end="|||")
                save_as("./output/updates_text.txt",updates_df,sep=":::",end="|||")
                save_as("./output/authors_text.txt",authors_df,sep=":::",end="|||")
                urls.pop(0)
                with open("./kickstarterUrls_remaining.txt", "w") as file:
                    file.write(','.join(urls))
            else:
                print("Not saved dataframes.")
                print("projects_df empty: ",projects_df.empty)
                print("rewards_df empty: ",rewards_df.empty)
                print("updates_df empty: ",updates_df.empty)
                print("authors_df empty: ",authors_df.empty)
            sleeptime = random.randint(2.0,10.0)
            print("next call wait until", sleeptime)
            time.sleep(1.0 * sleeptime)
    except Exception as e: 
        with open("/Users/cheenu/Desktop/Kickstarter Scraper/kickstarterUrls_exceptions.txt", "a+") as file:
            file.write(current_url + ':' + str(e) + '\n')
        urls.pop(0)
        with open("/Users/cheenu/Desktop/Kickstarter Scraper/kickstarterUrls_remaining.txt", "w") as file:
            file.write(','.join(urls))
        print(e)
        print("\n" + str(len(urls)) + " urls remaining.")
    finally:
        print("Sleeping... Trying after 15 mins...")
        time.sleep(60.0 * 15)
