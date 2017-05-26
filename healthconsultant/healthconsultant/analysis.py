#encoding=utf-8
import jieba
import jieba.analyse
import operator
from datetime import datetime
import json
import os
import yaml
import io

class Consultant:

    def ask(self,query):
        #max number of recommended article
        max_article = 15
        is_build_file_tag_to_article_id = True  #True: build tag to article_id in real time and write into file
                            #False: get tag to article_id by reading file
        is_build_file_tag_to_article_info = False
        is_build_file_tag_to_article_id_by_file_tag_to_article_info = True
        #word which will not be used to query article
        black_list = {u"想要",u"請問",u"如何",u"疑問",u"怎麼",u"為何",u"根據",u"因為",u"醫生"}

        #set dictionary to split sentence into words
        #os.path.dirname(__file__) => get path of diretory which this file is in
        #os.path.dirname(os.path.dirname(__file__)) => get path of directory of diretory which this file is in
        jieba_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/dict_refined.txt.big')
        jieba.set_dictionary(jieba_path)
        #jieba.set_dictionary('./data/dict.txt.big')
        article_list = []
        h2sync_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/articles_h2sync.txt')
        huangrh_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/articles_huangrh.txt')
        diabetes_and_me_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'data/articles_diabetes_and_me.txt')
        tag_to_article_info_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),'data/tag_to_article_info.txt')


        print "start read article:" + str(datetime.now())
        # parse articles into article list


        # read file
        with open(h2sync_path) as data_file:
            data = json.load(data_file)
        for index in range(len(data['data'])):
            article_list.append(data['data'][index])
        # read file
        with open(huangrh_path) as data_file:
            data = json.load(data_file)
        for index in range(len(data['data'])):
            article_list.append(data['data'][index])

        # read file
        file_diabetes_and_me_path= open(diabetes_and_me_path, 'r+')
        lines_diabetes_and_me_path = file_diabetes_and_me_path.readlines()
        temp_title = ""
        temp_summary = ""
        line_type = 0 # 0:title  1:siummay
        selfadd_index = 0
        for line in lines_diabetes_and_me_path:
            #print line
            if line == "title\n":
                line_type = 0
                if selfadd_index > 0:
                    #add article
                    article = {}
                    article['title'] = temp_title
                    article['summary'] = temp_summary
                    article['source'] = "衛生福利部國民健康署<糖尿病與我>"
                    article_list.append(article)
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
                article_list.append(article)
            else:
                if line_type == 0:
                    temp_title = temp_title + line
                else:
                    temp_summary = temp_summary + line
            selfadd_index += 1

        print "finish read article:"+str(datetime.now())

        #establish mapping of tag and article_id (many to many relationship)
        tag_to_article_ids = {}
        index_article = 0

        if is_build_file_tag_to_article_info:
            tag_to_article_info_list = []
            for article in article_list:
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
                tag_to_article_info_list.append(article_new)

            #wirte file
            with io.open(tag_to_article_info_path, 'w', encoding='utf8') as file_tag_to_article_info:
                yaml.dump(tag_to_article_info_list, file_tag_to_article_info, default_flow_style=False, allow_unicode=True)

        if is_build_file_tag_to_article_id:
            if is_build_file_tag_to_article_id_by_file_tag_to_article_info:
                print "start to build tag to article id based on file tag_to_article_info:" + str(datetime.now())
                with open(tag_to_article_info_path, 'r') as file_tag_to_article_info:
                    try:
                        article_list = yaml.load(file_tag_to_article_info)
                    except yaml.YAMLError as exc:
                        print(exc)
                print article_list[0]
            else:
                print "start building tag to article id based on origin files:" + str(datetime.now())
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
            print "finish building tag to article id:" + str(datetime.now())


        print "start to read file tag_to_article_id:" + str(datetime.now())
        tag_to_id_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data/tag_to_id.txt')
        f=open(tag_to_id_path,'r+')
        lines=f.readlines()
        for line in lines:
            line = line.decode('utf-8')
            fragment = line.split(":")
            #print fragment
            mapping = {fragment[0]:fragment[1]}
            tag_to_article_ids.update(mapping)
        print "finish reading file tag_to_article_id:" + str(datetime.now())


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
        print len(article_list)
        for id_and_score in sorted_article_id_to_score:

            if count > max_article:
                break

            id = id_and_score[0]
            result.append(article_list[int(id)])
            count += 1
        #print "finish getting result:"+str(datetime.now())
        return result
