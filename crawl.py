import pickle
import pprint

from selenium import webdriver


class Crawler:
    def __init__(self, serializer):
        self.serializer = serializer
        self.root = "http://www.politifact.com/personalities/"
        self.base = "http://www.politifact.com/"
        self.driver = webdriver.Firefox()
        self._safe_get(self.root)
        self.valid = ['democrat', 'republican', 'independent']
        self.links_path = 'data/links.pickle'
        self.results_path = 'data/results.pickle'

    def _safe_get(self, url):
        try:
            self.driver.set_page_load_timeout(15)
            self.driver.get(url)
        except Exception as e:
            print(e)
            self.driver.set_page_load_timeout(30)

    def _safe_click(self, element):
        try:
            self.driver.set_page_load_timeout(15)
            element.click()
        except Exception as e:
            print(e)
            self.driver.set_page_load_timeout(30)

    def collect(self):
        try:
            elems = self.driver.find_elements_by_css_selector("li .az-list__item")
            links = []
            for index, elem in enumerate(elems):
                print(index, '-', len(elems))
                spans = elem.find_elements_by_css_selector('span')
                if spans and spans[0].text.lower() in self.valid:
                    links.append({
                        'link': elem.find_element_by_css_selector('a').get_attribute('href'),
                        'affiliation': spans[0].text.lower()
                    })

            self.serializer.dump(links, open(self.links_path, 'wb'))

            results = []
            for index, link in enumerate(links):
                print(index, '-', len(links))
                result = self.visit(link)
                new_result = []
                for r in result:
                    r['affiliation'] = link['affiliation']
                    new_result.append(r)
                pprint.pprint(new_result)
                results += new_result
                self.serializer.dump(results, open(self.results_path, 'wb'))
        except:
            self.driver.close()
            raise

    def visit(self, url):
        self._safe_get(url['link'] + 'statements/by')
        data = self.visit_page()
        _next = self._try_get_next_link()
        while _next:
            self._safe_click(_next)
            data += self.visit_page()
            _next = self._try_get_next_link()
        return data

    def _try_get_next_link(self):
        try:
            return self.driver.find_element_by_css_selector('.step-links__next')
        except:
            return None

    def visit_page(self):
        # Get all statements
        statements = self.driver.find_elements_by_css_selector('.statement')
        data = []
        for statement in statements:
            data.append(self.parse_statement(statement))
        return data

    def parse_statement(self, element):
        # Get mugshot
        data = {}
        data['mugshot'] = element.find_element_by_css_selector('.mugshot img').get_attribute('src')
        data['source'] = element.find_element_by_css_selector('.statement__source a').text
        data['text'] = element.find_element_by_css_selector('.statement__text a').text
        data['edition'] = element.find_element_by_css_selector('.statement__edition a').text
        data['date'] = element.find_element_by_css_selector('.statement__edition span').text
        data['rating'] = element.find_element_by_css_selector('.meter img').get_attribute('alt')
        data['reason'] = element.find_element_by_css_selector('.meter .quote').text
        return data


Crawler(serializer=pickle).collect()
