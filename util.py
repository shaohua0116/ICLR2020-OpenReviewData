import numpy as np
import h5py
import string

# Meta data of papers
class PaperMeta(object):
    def __init__(self, title, abstract, keyword, rating, url, 
                 withdrawn, desk_reject, decision, # review=None, 
                 review_len=None):
        self.title = title             # str
        self.abstract = abstract       # str
        self.keyword = keyword         # list[str]
        self.rating = rating           # list[int]
        self.url = url                 # str
        self.withdrawn = withdrawn     # bool
        self.desk_reject = desk_reject # bool       
        self.decision = decision       # str
        # self.review = review           # list[str]
        self.review_len = review_len   # list[int]
        
        if len(self.rating) > 0:
            self.average_rating = np.mean(rating)
        else:
            self.average_rating = -1

            
class Keyword(object):
    def __init__(self, keyword, frequency, rating):
        self.keyword = keyword         # list[str]
        self.frequency = frequency     # int
        self.rating = rating           # list[int]        
    
    def average_rating(self):
        if len(self.rating) > 0:
            return np.mean(self.rating)
        else:
            return -1
    
    def update_frequency(self, frequency):
        self.frequency += frequency
        
    def update_rating(self, rating):
        self.rating = np.concatenate((self.rating, rating))
            
            
def write_meta(meta_list, filename):
    f = h5py.File(filename, 'w')
    for i, m in enumerate(meta_list):
        grp = f.create_group(str(i))
        grp['title'] = m.title
        grp['abstract'] = m.abstract
        grp['keyword'] = '#'.join(m.keyword)
        grp['rating'] = m.rating
        grp['url'] = m.url
        grp['withdrawn'] = m.withdrawn 
        grp['desk_reject'] = m.desk_reject         
        grp['decision'] = m.decision
        # grp['review'] = m.review        
        grp['review_len'] = m.review_len                
    f.close()
    
    
def read_meta(filename):
    f = h5py.File(filename, 'r')
    meta_list = []
    for k in list(f.keys()):
        meta_list.append(PaperMeta(
            f[k]['title'].value, 
            f[k]['abstract'].value, 
            f[k]['keyword'].value.split('#'),
            f[k]['rating'].value,
            f[k]['url'].value,
            f[k]['withdrawn'].value,            
            f[k]['desk_reject'].value,                        
            f[k]['decision'].value,
            # f[k]['review'].value if 'review' in list(f[k].keys()) else None,
            f[k]['review_len'].value if 'review_len' in list(f[k].keys()) else None,      
        ))
    return meta_list


def crawl_meta(meta_hdf5=None, write_meta_name='data.hdf5', crawl_review=False):
    
    if meta_hdf5 is None:
        # Crawl the meta data from OpenReview
        # Set up a browser to crawl from dynamic web pages 
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # from pyvirtualdisplay import Display
        # display = Display(visible=0, size=(800, 800))
        # display.start()
        
        import time
        executable_path = '/usr/local/bin/chromedriver'
        options = Options()
        options.add_argument("--headless")
        browser = webdriver.Chrome(options=options, executable_path=executable_path)            
    
        # Load all URLs for all ICLR submissions
        urls = []
        with open('urls.txt') as f:
            urls = f.readlines()
        urls = [url.strip() for url in urls]
        
        meta_list = [] 
        wait_time = 0.25
        max_try = 1000
        for i, url in enumerate(urls):
            browser.get(url)
            time.sleep(wait_time)
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
            # keyword
            if 'Keywords:' in key:
                keyword = value[key.index('Keywords:')].split(',')
                keyword = [k.strip(' ') for k in keyword]
                keyword = [''.join(string.capwords(k).split(' ')) for k in keyword if not k == '']
                for j in range(len(keyword)):
                    if '-' in keyword[j]:
                        keyword[j] = ''.join([string.capwords(kk) for kk in keyword[j].split('-')])       
            else:
                keyword = []
            # rating
            rating_idx = [i for i, x in enumerate(key) if x == "Rating:"]
            rating = []
            if len(rating_idx) > 0:
                for idx in rating_idx:
                    rating.append(int(value[idx].split(":")[0]))
                    
            if crawl_review:
                review_idx = [i for i, x in enumerate(key) if x == "Review:"]
                # review = []
                review_len = []
                if len(review_idx) > 0:
                    for idx in review_idx:
                        review_len.append(len([w for w in value[idx].replace('\n', ' ').split(' ') if not w == '']))
                        # review.append(value[idx])
            # decision
            if 'Recommendation:' in key:
                decision = value[key.index('Recommendation:')]
            else:
                decision = 'N/A'
            
            # log
            log_str = '[{}] Abs: {} chars, keywords: {}, ratings: {}'.format(
                i+1, len(abstract), len(keyword), rating,
            )
            if crawl_review:
                log_str += ', review len: {}'.format(review_len)
            if not decision == 'N/A':
                log_str += ', decision: {}'.format(decision)
            log_str += '] {}'.format(title)

            if withdrawn:
                log_str += ' (withdrawn)'
            if desk_reject:
                log_str += ' (desk_reject)'
            print(log_str)
            
            meta_list.append(PaperMeta(
                title, abstract, keyword, rating, url,                        
                withdrawn, desk_reject, decision,
                # None if not crawl_review else review,
                None if not crawl_review else review_len,                    
            ))
            
        # Save the crawled data
        write_meta(meta_list, write_meta_name)
    else:
        # Load the meta data from local
        meta_list = read_meta(meta_hdf5)
    return meta_list
