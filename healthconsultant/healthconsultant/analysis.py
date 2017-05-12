#encoding=utf-8
import jieba
import jieba.analyse
import operator
from datetime import datetime
import json
import os

class Consultant:

    def ask(self,query):
        #max number of recommended article
        max_article = 15
        isBuildTag = False  #True: build tag to article_id in real time and write into file
                            #False: get tag to article_id by reading file
        #word which will not be used to query article
        black_list = {"想要","請問","如何","疑問","怎麼","為何","根據","因為","醫生"}

        #set dictionary to split sentence into words
        #os.path.dirname(__file__) => get path of diretory which this file is in
        #os.path.dirname(os.path.dirname(__file__)) => get path of directory of diretory which this file is in
        jieba_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/dict.txt.big')
        jieba.set_dictionary(jieba_path)
        #jieba.set_dictionary('./data/dict.txt.big')

        print "start read article:"+str(datetime.now())
        #parse articles into article list
        article_list = []

        h2sync_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/h2sync.txt')
        huangrh_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/huangrh.txt')
        selfadd_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/selfadd.txt')
        # read file
        with open(h2sync_path) as data_file:
            data = json.load(data_file)
        for index in range(len(data['data'])):
            article_list.append(data['data'][index])

        with open(huangrh_path) as data_file:
            data = json.load(data_file)
        for index in range(len(data['data'])):
            article_list.append(data['data'][index])

        file_selfadd= open(selfadd_path, 'r+')
        lines_selfadd = file_selfadd.readlines()
        temp_title = ""
        temp_summary = ""
        type = 0 # 0:title  1:siummay
        selfadd_index = 0
        for line in lines_selfadd:
            #print line
            if line == "title\n":

                if selfadd_index >0:
                    #add article
                    article = {}
                    article['title'] = temp_title
                    article['summary'] = temp_summary
                    article_list.append(article)
                    temp_title = ""
                    temp_summary = ""

                type = 0
            elif line == "summary\n":
                type = 1
            elif line == "end":

                # add last article
                article = {}
                article['title'] = temp_title
                article['summary'] = temp_summary
                article_list.append(article)
            else:
                if type == 0:
                    temp_title = temp_title + line
                else:
                    temp_summary = temp_summary + line
            selfadd_index += 1

        print "finish read article:"+str(datetime.now())

        #establish mapping of tag and article_id (many to many relationship)
        tag_to_article_ids = {}
        index_article = 0
        if isBuildTag == True:
            for article in article_list:
                #print article
                #Each article will only extract 10 tags which are top 10 highest weight
                #it uses tf-idf to calculte weight. tf is based on this article, idf here is based on jieba database
                tags = jieba.analyse.extract_tags(article['title'], 10)
                for tag in tags:

                    if tag not in black_list:
                        if tag_to_article_ids.has_key(tag):
                            tag_to_article_ids[tag] = tag_to_article_ids[tag] + ","+str(index_article)
                        else:
                            tag_to_article_ids[tag] = str(index_article)

                tags = jieba.analyse.extract_tags(article['summary'], 10)
                for tag in tags:

                    if tag not in black_list:
                        if tag_to_article_ids.has_key(tag):
                            tag_to_article_ids[tag] = tag_to_article_ids[tag] + "," + str(index_article)
                        else:
                            tag_to_article_ids[tag] = str(index_article)

                index_article+=1
                tag_to_id_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/tag_to_id.txt')
                f=open(tag_to_id_path,'w+')
                for tag in tag_to_article_ids.keys():
                    f.write(tag.encode('utf-8')+":".encode('utf-8')+tag_to_article_ids.get(tag).encode('utf-8')+"\n".encode('utf-8'))

        else:
            tag_to_id_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/tag_to_id.txt')
            f=open(tag_to_id_path,'r+')
            lines=f.readlines()
            for line in lines:
                line = line.decode('utf-8')
                fragment = line.split(":")
                #print fragment
                mapping = {fragment[0]:fragment[1]}
                tag_to_article_ids.update(mapping)

        print "finish building tag to article id:"+str(datetime.now())

        #split sentence of question into words with weight
        #higher weight means more important in this sentence(query)
        #it uses tf-idf . tf is based on this sentence, idf here is based on jieba database
        keywords_with_weight = jieba.analyse.extract_tags(query, 10,withWeight=True)



        article_id_to_score = {}

        #tag_to_article_ids = tag_to_article_ids_new
        for keyword_with_weight in keywords_with_weight:
            keyword = keyword_with_weight[0]
            weight = keyword_with_weight[1]

            #1.single word will not be used to query article
            #2.word in black_list will not be used to query article
            if (len(keyword) >1) and (keyword not in black_list):

                if tag_to_article_ids.has_key(keyword):

                    id_string = tag_to_article_ids.get(keyword).split(',')
                    for id in id_string:
                        if id not in article_id_to_score.keys():
                            article_id_to_score[id] = weight
                        else:   #let article which contain more than two keyword have more score
                            article_id_to_score[id] += weight

        print "finish building article_id_to_score:"+str(datetime.now())

        #sort article by score
        sorted_article_id_to_score= sorted(article_id_to_score.items(), key=operator.itemgetter(1),reverse=True)

        #use id to get content of article
        count = 0
        result = []
        for id_and_score in sorted_article_id_to_score:

            if count > max_article:
                break

            id = id_and_score[0]
            result.append(article_list[int(id)])
            count += 1
        #print "finish getting result:"+str(datetime.now())
        return result
