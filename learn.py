import re
import nltk
import pickle
import pprint
from nltk.classify import NaiveBayesClassifier

DATA_PATH = 'data/cleaned.pickle'


class Bayesian:

    def __init__(self, serializer, data_path):
        self.serializer = serializer
        self.data_path = data_path
        self.data = self.serializer.load(open(data_path, 'rb'))
        self.positive_words = ['good', 'great', 'amazing', 'wonderful', 'best', 'awesome', 'outstanding',
                               'fantastic', 'terrific', 'nice']
        self.negative_words = ['bad', 'terrible', 'awful', 'ugly', 'horrible', 'horrid', 'disgusting', 'useless',
                               'hate', 'evil', 'stupid', 'dumb', 'idiotic', 'idiot']
        self.neutral_words = ['the', 'is', 'was', 'did', 'know', 'words', 'and', 'do', 'but', 'also', 'quite']

        self.positive_ratings = ['true', 'mostly true', 'no flip']
        self.negative_ratings = ['false', 'mostly false', 'pants on fire!', 'full flop']
        self.neutral_ratings = ['half-true', 'half flip']

    def _get_quote_data(self):
        # only care about quoted words
        quoted = []
        for claim in self.data:
            for quote in re.findall(r'".*?"', claim['text']):
                quoted.append({
                    'text': quote,
                    'affiliation': claim['affiliation'],
                    'rating': claim['rating']
                })
        return quoted

    def _get_words(self, quote):
        # return nltk.word_tokenize(quote)
        return [i.lower() for i in quote.split(' ')]

    def word_features(self, words):
        return dict([(word, True) for word in words])

    def train_ratings(self):
        true_features = []
        false_features = []
        neutral_features = []
        self.quoted_data = self._get_quote_data()
        for quote in self._get_training_set():
            for word in self._get_words(quote['text']):
                if quote['rating'] in self.positive_ratings:
                    true_features.append((self.word_features(word), 'true'))
                elif quote['rating'] in self.negative_ratings:
                    false_features.append((self.word_features(word), 'false'))
                elif quote['rating'] in self.neutral_ratings:
                    neutral_features.append((self.word_features(word), 'neutral'))
                else:
                    raise Exception(f"Could not find category for quote with rating: {quote['rating']}")

        training_set = false_features + true_features + neutral_features

        self.classifier = NaiveBayesClassifier.train(training_set)

    def train_sentiment(self):
        self.quoted_data = self._get_quote_data()
        self.test_set = self._clean(self.quoted_data)
        positive_features = [(self.word_features(pos), 'true') for pos in self.positive_words]
        negative_features = [(self.word_features(neg), 'false') for neg in self.negative_words]
        neutral_features = [(self.word_features(neu), 'neutral') for neu in self.neutral_words]

        training_set = negative_features + positive_features + neutral_features

        self.classifier = NaiveBayesClassifier.train(training_set)

    def _get_training_set(self):
        self.training_set = []
        self.test_set = []
        positive = 0
        negative = 0
        neutral = 0
        for i in self._clean(self.quoted_data):
            if len(self.training_set) > len(self.quoted_data) // 2:
                self.test_set.append(i)
            elif positive <= negative and positive <= neutral and i['rating'] in self.positive_ratings:
                self.training_set.append(i)
                positive += 1
            elif negative <= positive and negative <= neutral and i['rating'] in self.negative_ratings:
                self.training_set.append(i)
                negative += 1
            elif neutral <= positive and neutral <= negative and i['rating'] in self.neutral_ratings:
                self.training_set.append(i)
                neutral += 1
            else:
                self.test_set.append(i)
        return self.training_set

    def _clean(self, data):
        for quote in data:
            quote['text'] = quote['text'].replace('"', '').replace(',', '').replace('.', '').lower()
        return data

    def test(self):
        data = {
            'correct': 0,
            'incorrect': 0,
            'correct_positive': 0,
            'correct_negative': 0,
            'correct_neutral': 0,
            'incorrect_p_neg_actual_pos': 0,
            'incorrect_p_neg_actual_neut': 0,
            'incorrect_p_neut_actual_pos': 0,
            'incorrect_p_neut_actual_neg': 0,
            'incorrect_p_pos_actual_neg': 0,
            'incorrect_p_pos_actual_neut': 0,
            'positive_predictions': 0,
            'negative_predictions': 0,
            'neutral_predictions': 0,
        }
        for quote in self.test_set:
            result = self.test_quote(quote['text'])
            if result['true'] > result['false']:
                prediction = 'true'
                data['positive_predictions'] += 1
            elif result['true'] < result['false']:
                prediction = 'false'
                data['negative_predictions'] += 1
            else:
                prediction = 'neutral'
                data['neutral_predictions'] += 1

            if prediction == 'true' and quote['rating'] in self.positive_ratings:
                data['correct'] += 1
                data['correct_positive'] += 1
            elif prediction == 'false' and quote['rating'] in self.negative_ratings:
                data['correct'] += 1
                data['correct_negative'] += 1
            elif prediction == 'neutral' and quote['rating'] in self.neutral_ratings:
                data['correct'] += 1
                data['correct_neutral'] += 1
            elif prediction == 'false' and quote['rating'] in self.positive_ratings:
                data['incorrect_p_neg_actual_pos'] += 1
                data['incorrect'] += 1
            elif prediction == 'false' and quote['rating'] in self.neutral_ratings:
                data['incorrect_p_neg_actual_neut'] += 1
                data['incorrect'] += 1
            elif prediction == 'neutral' and quote['rating'] in self.positive_ratings:
                data['incorrect_p_neut_actual_pos'] += 1
                data['incorrect'] += 1
            elif prediction == 'neutral' and quote['rating'] in self.negative_ratings:
                data['incorrect_p_neut_actual_neg'] += 1
                data['incorrect'] += 1
            elif prediction == 'true' and quote['rating'] in self.negative_ratings:
                data['incorrect_p_pos_actual_neg'] += 1
                data['incorrect'] += 1
            elif prediction == 'true' and quote['rating'] in self.neutral_ratings:
                data['incorrect_p_pos_actual_neut'] += 1
                data['incorrect'] += 1
            else:
                data['incorrect'] += 1

        return data

    def test_quote(self, quote):
        words = quote.split(' ')
        neg = 0
        pos = 0
        for word in words:
            class_result = self.classifier.classify(self.word_features(word.lower()))
            if class_result == 'false':
                neg = neg + 1
            if class_result == 'true':
                pos = pos + 1
        return {
            'true': pos / len(words),
            'false': neg / len(words)
        }

b = Bayesian(serializer=pickle, data_path=DATA_PATH)
b.train_ratings()
pprint.pprint(b.test())
