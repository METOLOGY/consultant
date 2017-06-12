#encoding=utf-8
import jieba
import jieba.analyse
import operator
from datetime import datetime
import json
import os
import yaml
import io
import codecs

class Consultant:

    global h2sync_path
    global huangrh_path
    global diabetes_and_me_path
    global article_with_tags_path
    global tag_to_article_ids_path
    global max_article
    global jieba_dict_path
    global black_list

    h2sync_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/articles_h2sync.txt')
    huangrh_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/articles_huangrh.txt')
    diabetes_and_me_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'data/articles_diabetes_and_me.txt')

    article_with_tags_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'data/tag_to_article_info.yml')
    tag_to_article_ids_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/tag_to_id.txt')
    max_article = 15

    #set dictionary to split sentence into words
    #os.path.dirname(__file__) => get path of diretory which this file is in
    #os.path.dirname(os.path.dirname(__file__)) => get path of directory of diretory which this file is in
    jieba_dict_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/dict_refined.txt.big')

    #word which will not be used to query article
    black_list = {u"想要",u"請問",u"如何",u"疑問",u"怎麼",u"為何",u"根據",u"因為",u"醫生"}



    def read_articles(self):
        articles = []
        # read file
        with open(h2sync_path) as data_file:
            data = json.load(data_file)
        for index in range(len(data['data'])):
            articles.append(data['data'][index])
        # read file
        with open(huangrh_path) as data_file:
            data = json.load(data_file)
        for index in range(len(data['data'])):
            articles.append(data['data'][index])

        # read file
        file_diabetes_and_me_path= open(diabetes_and_me_path, 'r+')
        lines_diabetes_and_me_path = file_diabetes_and_me_path.readlines()
        temp_title = ""
        temp_summary = ""
        line_type = 0 # 0:title  1:siummay
        self_add_index = 0
        for line in lines_diabetes_and_me_path:
            #print line
            if line == "title\n":
                line_type = 0
                if self_add_index > 0:
                    #add article
                    article = {}
                    article['title'] = temp_title
                    article['summary'] = temp_summary
                    article['source'] = "衛生福利部國民健康署<糖尿病與我>"
                    articles.append(article)
                    temp_title = ""
                    temp_summary = ""

            elif line == "summary\n":
                line_type = 1
            elif line == "end":
                # add last article
                article = {}
                article['title'] = temp_title
                article['summary'] = temp_summary
                article['source'] = "衛生福利部國民健康署<糖尿病與我>"
                articles.append(article)
            else:
                if line_type == 0:
                    temp_title = temp_title + line
                else:
                    temp_summary = temp_summary + line
            self_add_index += 1

        print "finish read article:"+str(datetime.now())
        return articles

    def build_articles_with_tags(self,articles_without_tags):
        articles_with_tags = []
        for article in articles_without_tags:
            article_tag_list = []
            tags = jieba.analyse.extract_tags(article['title'], 10)
            for tag in tags:
                if tag not in article_tag_list:
                    article_tag_list.append(tag)
            tags = jieba.analyse.extract_tags(article['summary'], 10)
            for tag in tags:
                if tag not in article_tag_list:
                    article_tag_list.append(tag)
            article_new = article
            article_new['tag'] = article_tag_list
            articles_with_tags.append(article_new)

        #wirte file
        #with io.open(article_with_tags_path, 'w', encoding='utf8') as file_tag_to_article_info:
            #yaml.dump(tag_to_article_info_list, file_tag_to_article_info, default_flow_style=False, allow_unicode=True)
        return articles_with_tags

    def read_articles_with_tags(self):
        with codecs.open(article_with_tags_path, 'r',encoding = 'utf-8') as file_tag_to_article_info:
            try:
                articles_with_tags = yaml.load(file_tag_to_article_info)
            except yaml.YAMLError as exc:
                print(exc)
        print len(articles_with_tags)
        return articles_with_tags

    def build_tag_to_article_ids(self,articles_with_tags):
        index_article = 0
        tag_to_article_ids = {}
        print "start to build tag to article id:" + str(datetime.now())
        for article in articles_with_tags:
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

            index_article += 1

        print "finish building tag to article id:" + str(datetime.now())

        f = open(tag_to_article_ids_path,'w+')
        for tag in tag_to_article_ids.keys():
            f.write(tag.encode('utf-8')+":".encode('utf-8')+tag_to_article_ids.get(tag).encode('utf-8')+"\n".encode('utf-8'))
        print "finish writing file of tag_to_article_ids:" + str(datetime.now())

    def read_tag_to_article_ids(self):

        tag_to_article_ids = {}
        file_tag_to_article_ids = codecs.open(tag_to_article_ids_path, 'r+',encoding = 'utf-8')
        lines_tag_to_article_ids = file_tag_to_article_ids.readlines()

        for line in lines_tag_to_article_ids:
            tag_to_article_ids[line.split(":")[0]] = line.split(":")[1]

        print len(tag_to_article_ids)
        return tag_to_article_ids


    def ask(self,query):
        print jieba_dict_path
        jieba.set_dictionary(jieba_dict_path)


        articles_without_tags = []
        articles_without_tags = self.read_articles()

        #establish mapping of tag and article_id (many to many relationship)
        #build_articles_with_tags(articles_without_tags)
        tag_to_article_ids = {}

        articles_with_tags = []
        articles_with_tags = self.read_articles_with_tags()
        self.build_tag_to_article_ids(articles_with_tags)
        tag_to_article_ids = self.read_tag_to_article_ids()

        #split sentence of question into words with weight
        #higher weight means more important in this sentence(query)
        #it uses tf-idf . tf is based on this sentence, idf here is based on jieba database
        keywords_with_weight = jieba.analyse.extract_tags(query, 10, withWeight=True)

        article_id_to_score = {}

        #tag_to_article_ids = tag_to_article_ids_new
        for keyword_with_weight in keywords_with_weight:
            keyword = keyword_with_weight[0]
            weight = keyword_with_weight[1]
            #print keyword,":",weight
            #1.single word will not be used to query article
            #2.word in black_list will not be used to query article
            if (len(keyword) >1) and (keyword not in black_list):
                #print "key:",keyword,":",weight
            #    keyword = keyword.encode('utf-8')
                if tag_to_article_ids.has_key(keyword):
                    #print "has_key:",keyword,":",weight
                    id_string = tag_to_article_ids.get(keyword).split(',')
                    for id in id_string:
                        if id not in article_id_to_score.keys():
                            article_id_to_score[id] = weight
                        else:   #let article which contain more than two keyword have more score
                            article_id_to_score[id] += weight

        print "finish building article_id_to_score:"+str(datetime.now())
        print "sorting!!"
        #sort article by score
        sorted_article_id_to_score = sorted(article_id_to_score.items(), key=operator.itemgetter(1),reverse=True)

        #use id to get content of article
        count = 0
        result = []

        for id_and_score in sorted_article_id_to_score:

            if count > max_article:
                break

            id = id_and_score[0]
            print id,":" ,str(int(id))
            print articles_with_tags[int(id)]
            result.append(articles_with_tags[int(id)])
            count += 1
        #print "finish getting result:"+str(datetime.now())
        return result
