from flask import Flask, send_from_directory, request
from werkzeug.utils import secure_filename
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS, cross_origin
import random
import os

app = Flask(__name__, static_url_path='', static_folder='frontend/build')
app.config['UPLOAD_FOLDER'] = os.getcwd()
CORS(app) #comment this on deployment
api = Api(app)

@app.route("/", defaults={'path':''})
def serve(path):
    return send_from_directory(app.static_folder,'index.html')


def process_questions(PATH, n_q, time):
    with open(PATH) as f:
        lines_1 = f.readlines()
    lines_2 = [x for x in lines_1 if not x.startswith(('*', '\n'))]
    lines = [line.rstrip() for line in lines_2]
    q_and_a = {}

    def generate_dict():
        i = 1
        counter = 0
        while (i < len(lines)):
            i = parse_question(lines, i, counter)
            i += 1
            counter += 1

        q_list = q_and_a.keys()
        return list(q_list), len(q_list)

    def parse_question(l, i, counter):
        arr = []
        j = i
        while (l[j][:2] != '@E'):
            arr.append(l[j])
            j += 1
        q_and_a[str(counter)] = arr
        return j

    questions, total = generate_dict()
    if (n_q > total):
        n_q = total

    def get_random_q():
        return random.choice(range(total))

    rand_questions = []
    while (len(rand_questions) < n_q):
        val = get_random_q()
        if questions[val] not in rand_questions:
            rand_questions.append(questions[val])

    def format_question(q):
        lines = q.split('\n')
        out = ""
        for line in lines:
            out += line
            out += " "
        return out

    def parse_question_two(arr):
        if arr[0][:2] == "@Q":
            i = 1
        else:
            i = 0
        ques = "Q"+str(int(key)+1)+": "
        while (arr[i][:2] != "@A"):
            ques += arr[i]
            ques += "\n"
            i += 1
        return format_question(ques), i

    QUESTIONS = []
    OPTIONS = []
    ANSWERS = []
    OUT = []

    for key in rand_questions:
        arr = q_and_a[key]
        ques, ans_i = parse_question_two(arr)
        ans = int(arr[ans_i+1])
        opts = arr[ans_i+2:]
        out = {}
        out['question'] = ques
        out['answers'] = opts
        out['correctAnswerIndex'] = ans

        OUT.append(out)
        QUESTIONS.append(ques)
        ANSWERS.append(ans)
        OPTIONS.append(opts)

    return [OUT, n_q, time]


@app.route('/upload', methods=['POST'])
@cross_origin()
def fileUpload():
    try:
        target = os.path.join(app.config['UPLOAD_FOLDER'], 'question_files')
        if not os.path.isdir(target):
            os.mkdir(target)
        file = request.files['file']
        name = request.form['name']
        n_q = request.form['n_q']
        time = request.form['time']
        filename = secure_filename(file.filename)
        destination = "/".join([target, filename])
        file.save(destination)
    except Exception as e:
        response = {"status_code": "400", "message": "Error Uploading File"}
    
    try:
        output = process_questions(destination, int(n_q), time)
    except Exception as e:
        response = {"status_code": "400", "message": "Error Processing File"}
    print(file)
    return {"status": "200", "message": output}