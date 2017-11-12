from CourseScheduling.blueprints.schedule.dbHelper import getInfo, getMajorsNames, getMajorSpecsByName, getQuarterCodes
from flask import Blueprint, render_template, request
from CourseScheduling.blueprints.schedule.models import Course, Major
import lib.CourseSchedulingAlgorithm as cs
import ast
from CourseScheduling.blueprints.schedule import dgw_data
from CourseScheduling.blueprints.schedule.forms import HomeInputForm

schedule = Blueprint('schedule', __name__, template_folder='templates')

@schedule.route('/')
def index():
    return render_template('schedule/index.html')

@schedule.route('/input')
def schedule_home():
    """
    input page 1 for major selection
    """
    home_input_form = HomeInputForm()
    home_input_form.firstQuarter.choices=getQuarterCodes()
    majorNames = getMajorsNames()
    home_input_form.majors.choices=list(map(lambda x: (x,x), majorNames))
    return render_template('schedule/input.html',form=home_input_form)#, majordata=majordata)

@schedule.route('/detailedinput', methods=['POST', 'GET'])
def detailed_input():
    form = request.form
    major = form.getlist("major")[0].upper()
    print("MAJOR: " + major)
    return render_template('schedule/detailedinput.html',
                            specs=getMajorSpecsByName(major))


@schedule.route('/saveme')
def saveme():
    return render_template('schedule/saveme.html')

@schedule.route('/launch', methods=['POST', 'GET'])
def launch():
    cookie = request.form.getlist('cookie')[0]
    print (cookie)
    upper_units = 90
    max_widths = {0: 13, 'else': 16}
    startQ = 0
    avoid = set()

    d = dgw_data.data(cookie)
    d.fetch_xml()
    G, R, R_detail = dict(), dict(), dict()
    for mname in d.major:
        major = Major.objects(name=mname.upper()).first()
        if not major:
            continue
        g, r, r_detail = major.prepareScheduling(spec=d.spec, ge_filter=d.ge_table)
        G.update(g)
        R.update(r)
        R_detail.update(r_detail)

    taken = d.classes
    print (taken)
    # update requirement table based on the taken information
    cs.update_requirements(R_detail, R, taken)
    # construct CourseGraph. graph is labeled after init
    graph = cs.CourseGraph(G, r_detail=R_detail, R=R, avoid=avoid, taken=taken)
    # construct Schedule with width func requirements
    L = cs.Schedule(widths=max_widths)
    # construct the scheduling class
    generator = cs.Scheduling(start_q=startQ)
    # get the best schedule when the upper bound ranges from 0 to 10, inclusive.
    L, best_u, best_r = generator.get_best_schedule(graph, L, R, 0, 10)

    max_row_length = max(len(row) for row in L.L)

    # the parameters for render_template will be provided by CourseSchedulingAlgorithm:
    #   1,  L : best schedule generated by the algorithm
    #   2,  max_row_length : the max length of a row in this schedule

    #return render_template('schedule/output.html',
    #                       schedule=L, row_length=max_row_length)

    courses_preview = []
    for quarter in L.L:
        for course in quarter:
            courses_preview.append(course)
    courses_preview.sort()

    return render_template('schedule/preview.html',
                          courses=courses_preview, quarter=startQ, specialization=d.spec[0], taken=str(taken))



@schedule.route('/output', methods=['POST', 'GET'])
def schedule_output():
    print(request.form)
    #
    UNIVERSAL_REQUIREMENTS = {"University", "GEI", "GEII", "GEIII", "GEIV",
                    "GEV", "GEVI", "GEVII", "GEVIII"}
    CS_GENERAL_REQUIREMENTS = {"CS-Lower-division", "CS-Upper-division"}

    # user info should be private
    # also user info could be too large for GET request
    if request.method != 'POST':
        return render_template('schedule/input.html')

    form = request.form

    # input will be provided by POST request.
    # config upper standing units
    upper_units = 90
    # start quarter
    startQ = int(form.getlist("quarter")[0])
    # set of courses taken
    #taken = set(ast.literal_eval(form.getlist("finished")[0])) #{'MATH1B'}
    taken = set(ast.literal_eval(form.getlist("taken")[0]))
    # width setting
    max_widths = {0: 13, 'else': 16}
    # avoid
    avoid = set(ast.literal_eval(form.getlist("finished")[0])) #{'COMPSCI141'}
    #avoid = {}
    # union universal and cs general requirements (default)
    req = UNIVERSAL_REQUIREMENTS | CS_GENERAL_REQUIREMENTS
    if form.getlist("specialization"):
        req.add(form.getlist("specialization")[0])

    print(req)

    G, R, R_detail = getInfo(req)

    # update requirement table based on the taken information
    cs.update_requirements(R_detail, R, taken)
    # construct CourseGraph. graph is labeled after init
    graph = cs.CourseGraph(G, r_detail=R_detail, R=R, avoid=avoid, taken=taken)
    # construct Schedule with width func requirements
    L = cs.Schedule(widths=max_widths)
    # construct the scheduling class
    generator = cs.Scheduling(start_q=startQ)
    # get the best schedule when the upper bound ranges from 0 to 10, inclusive.
    L, best_u, best_r = generator.get_best_schedule(graph, L, R, 0, 10)

    max_row_length = max(len(row) for row in L.L)

    # the parameters for render_template will be provided by CourseSchedulingAlgorithm:
    #   1,  L : best schedule generated by the algorithm
    #   2,  max_row_length : the max length of a row in this schedule

    return render_template('schedule/output.html',
                           schedule=L, row_length=max_row_length)


@schedule.route('/preview', methods=['POST', 'GET'])
def schedule_preview():
    #
    UNIVERSAL_REQUIREMENTS = {"University", "GEI", "GEII", "GEIII", "GEIV",
                    "GEV", "GEVI", "GEVII", "GEVIII"}
    CS_GENERAL_REQUIREMENTS = {"CS-Lower-division", "CS-Upper-division"}

    # user info should be private
    # also user info could be too large for GET request
    if request.method != 'POST':
        return render_template('schedule/input.html')

    form = request.form

    # input will be provided by POST request.
    # config upper standing units
    upper_units = 90
    # start quarter
    startQ = int(form.getlist("quarter")[0])
    # width setting
    max_widths = {0: 200, 'else': 200}
    # union universal and cs general requirements (default)
    req = UNIVERSAL_REQUIREMENTS | CS_GENERAL_REQUIREMENTS

    spec = form.getlist("specialization")[0]
    req.add(spec)
    print(req)

    G, R, R_detail = getInfo(req)

    # update requirement table based on the taken information
    cs.update_requirements(R_detail, R, set())
    # construct CourseGraph. graph is labeled after init
    graph = cs.CourseGraph(G, r_detail=R_detail, R=R, avoid=set(), taken=set())
    # construct Schedule with width func requirements
    L = cs.Schedule(widths=max_widths)
    # construct the scheduling class
    generator = cs.Scheduling(start_q=startQ)
    # get the best schedule when the upper bound ranges from 0 to 10, inclusive.
    L, best_u, best_r = generator.get_best_schedule(graph, L, R, 0, 10)

    courses_preview = []
    for quarter in L.L:
        for course in quarter:
            courses_preview.append(course)
    courses_preview.sort()

    # the parameters for render_template will be provided by CourseSchedulingAlgorithm:
    #   1,  L : best schedule generated by the algorithm
    #   2,  max_row_length : the max length of a row in this schedule

    return render_template('schedule/preview.html',
                           courses=courses_preview, quarter=startQ, specialization=spec, taken="{}")
