from collections import defaultdict
from datetime import datetime
from math import floor
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras import models
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances


class TelegramAttackDetector:
    def __init__(self, language, participants_count):
        self.__participants = participants_count
        self.__language = language
        self.normal_frequency = floor(self.__participants ** 0.8 / 2 + 5)

        self.spam_model = models.load_model(f'./{self.__language}/spam_classification_model.keras')
        with open(f'./{self.__language}/tokenizer.pkl', 'rb') as handle:
            self.__tokenizer = pickle.load(handle)

        self.__participants_flag = False
        self.__frequency_flag = False
        self.__spam_flag = False

        self.__encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.__clusterer = DBSCAN(
            eps=0.7,
            min_samples=3,
            metric="precomputed",
        )

    def analyze_messages(self, current_participants, message_list):
        res_str = ''
        self.__check_participants(current_participants)
        self.__check_frequency(len(message_list))
        filtered_messages = self.__check_spam(message_list)
        print(f'filtered messages: {filtered_messages}')
        if self.__spam_flag:
            self.__check_frequency(len(filtered_messages))

        if self.__frequency_flag:
            cluster = self.__check_topic(filtered_messages)
            if len(filtered_messages) - len(cluster) <= self.normal_frequency:
                res_str = 'Information attack detected.\n'
            else:
                res_str = 'Suspicious activity detected.\n'
        else:
            if self.__spam_flag:
                res_str='Spam attack detected.\n'

        if self.__participants_flag:
            res_str += 'Suspicious number of users joined chat.'

        if res_str:
            res_str = '[' + datetime.now().strftime("%H:%M") + '] ' + res_str
            print(res_str)
        else:
            print('[' + datetime.now().strftime("%H:%M") + '] ' + 'No information attack')

        return res_str

    def __check_participants(self, current_participants):
        if self.__participants < 30:
          if current_participants - self.__participants >= 3:
              self.__participants_flag = True
        elif  self.__participants / current_participants >= 0.1:
            self.__participants_flag = True
        else:
            self.__participants_flag = False
        self.__participants = current_participants


    def __check_frequency(self, msg_length):
        self.normal_frequency = floor(self.__participants ** 0.8 / 2 + 5)
        if msg_length > self.normal_frequency:
            self.__frequency_flag = True
        else:
            self.__frequency_flag = False


    def __check_topic(self, messages):
        print(f'check_topic: {messages}')
        embeddings = self.__encoder.encode(messages)
        distance_matrix = cosine_distances(embeddings)
        labels = self.__clusterer.fit_predict(distance_matrix)
        clusters = defaultdict(list)
        for msg, label in zip(messages, labels):
            clusters[label].append(msg)

        largest_cluster_label = max(clusters, key=lambda lbl: len(clusters[lbl]))

        # 5. Print the results
        print("=== Clustered Topics ===")
        for cluster_id, msgs in clusters.items():
            if cluster_id == -1:
                print("\n[Noise / Outliers]:")
            else:
                print(f"\nTopic {cluster_id}:")
            for msg in msgs:
                print("  •", msg)

        return clusters[largest_cluster_label]




        # valid_clusters = {label: msgs for label, msgs in clusters.items() if label != -1}

        # if valid_clusters:
        #     largest_cluster_label = max(valid_clusters, key=lambda lbl: len(valid_clusters[lbl]))
        #     return valid_clusters[largest_cluster_label]
        # else:
        #     return clusters[-1]



    def __check_spam(self, messages):
        msg_seq = self.__tokenizer.texts_to_sequences(messages)
        msg_pad = pad_sequences(msg_seq, maxlen=100, padding='post', truncating='post')
        labels = self.spam_model.predict(msg_pad)
        labels = (labels > 0.5).astype(int)
        if 1 not in labels:
            self.__spam_flag = False
        else:
            self.__spam_flag = True
            print([msg for msg, label in zip(messages, labels) if label == 1])

        return [msg for msg, label in zip(messages, labels) if label == 0]

