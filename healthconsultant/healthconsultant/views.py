from django.http import HttpResponse
from django.http import JsonResponse

from django import template
from rest_framework.views import APIView
from healthconsultant.analysis import Consultant


class ConsoltantView(APIView):
    #for debug use: get all users
    def get(self, request, format=None):
        response_data = {}
        response_data["message"] = "home page"
        with open('templates/index.html','r') as reader:
                t= template.Template(reader.read())

        c= template.Context({'s':'s'})

        return HttpResponse(t.render(c))


    def post(self, request, format=None):
        response_data = {}
        response_data["message"] = "home page"
        with open('templates/index.html','r') as reader:
                t= template.Template(reader.read())

        question = request.data['question']
        consultant = Consultant()
        answer = consultant.ask(question)
        count = 0
        for info in answer:
            answer[count] = info.decode('utf-8')
            count+=1
        #print len(answer)

        c= template.Context({'answer':answer,'question':question})
        return HttpResponse(t.render(c))
