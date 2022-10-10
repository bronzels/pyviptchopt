from __future__ import print_function
import sys
#1,10
#100
#sys.setrecursionlimit(100000)#10000
import chardet
import time
import datetime
import random
import collections
import plotly as py
import plotly.figure_factory as ff
# Import Python wrapper for or-tools CP-SAT solver.
from ortools.sat.python import cp_model
#import pulp
#from pyscipopt import Model, quicksum

sys.setrecursionlimit(1000)
opt='ortools-cp-sat'
#opt='pyscipopt'

from libpycommon.common import mylog
mylogger = mylog.logger

dt = datetime.datetime
time_delta = datetime.timedelta
pyplt = py.offline.plot

class_slot_start_hour = 9
class_slot_cnt = 24
data_path = './vip_ttp_data/'

mul = 1
#mul = 10
#mul = 20
#mul = 50
#mul = 100
#mul = 6000

def load_text(file_name):
    try:
        with open(file_name, "rb") as f:
            f_read = f.read()
            f_cha_info = chardet.detect(f_read)
            final_data = f_read.decode(f_cha_info['encoding'])
            return final_data, True
    except FileNotFoundError:
        return str(None), False


def rgb():
    return random.randint(0, 255)

def split(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def cs_valid(weeks_day, today_weeks_day, slot, cal_start_slot):
    return weeks_day > today_weeks_day or (weeks_day == today_weeks_day and slot > cal_start_slot)

# print(data)
def TimeTableOpt(data_cfg, data_stu, data_tch):
    a_cfg = list(map(int, data_cfg.split()))
    tchcnt_stu = a_cfg[0]
    bonus_stu = a_cfg[1]
    tch_cnt = a_cfg[2]
    weeks_cnt = a_cfg[3]

    a_stu = list(map(int, data_stu.split()))
    student_type = collections.namedtuple('student_type', 'classes_per_week most_week_day most_slot quit_value rebuy_value l_teacher')
    field_cnt = 5 + tchcnt_stu
    stu_cnt = int(len(a_stu)/field_cnt)
    aa_stu = list(split(a_stu, field_cnt))
    a_tuple_stu = []
    #mul
    for i in range(mul):
        for i_a_stu in aa_stu:
            a_tuple_stu.append(student_type(
                classes_per_week=i_a_stu[0],
                most_week_day=i_a_stu[1],
                most_slot=i_a_stu[2],
                quit_value=i_a_stu[3],
                rebuy_value=i_a_stu[4],
                l_teacher=list(map(lambda tch: tch + tch_cnt * i, i_a_stu[5:]))
            ))

    a_tch_slot = list(map(int, data_tch.split()))
    tch_slot_type = collections.namedtuple('tch_slot_type', 'teacher_no weeks_day slot')
    aa_tch_slot = list(split(a_tch_slot, 4))
    a_tuple_tch_slot = []
    #cal_start_date = dt.today()
    cal_start_date = dt(2021,6,14,8,0)
    cal_start_slot = (max(cal_start_date.hour, class_slot_start_hour) - class_slot_start_hour)*2 + int(cal_start_date.minute / 30)
    if cal_start_slot >= class_slot_cnt:
        cal_start_date += time_delta(1)
        cal_start_date = dt(cal_start_date.year, cal_start_date.month, cal_start_date.day, class_slot_start_hour)
        cal_start_slot = 0
    else:
        cal_start_date = dt(cal_start_date.year, cal_start_date.month, cal_start_date.day, cal_start_slot+class_slot_start_hour)
    today_weeks_day = cal_start_date.weekday()
    d_tuple_tch_slot = {}
    for i in range(mul):
        for i_a_tch_slot in aa_tch_slot:
            weeks_day = i_a_tch_slot[1] * 7 + i_a_tch_slot[2]
            slot = i_a_tch_slot[3]
            if cs_valid(weeks_day, today_weeks_day, slot, cal_start_slot):
                d=weeks_day
                cs=slot
                t = i_a_tch_slot[0] + tch_cnt * i
                a_tuple_tch_slot.append(tch_slot_type(
                    teacher_no=t,
                    weeks_day=d,
                    slot=cs
                ))
                d_tuple_tch_slot[(d,cs,t)] = 1

    #mul
    tch_cnt = tch_cnt*mul
    stu_cnt = stu_cnt*mul
    mylogger.info('stu_cnt:{}, tchcnt_stu:{}, bonus_stu:{}, tch_cnt:{}, weeks_cnt:{}'.format(stu_cnt, tchcnt_stu, bonus_stu, tch_cnt, weeks_cnt))

    # Create the model.
    model = cp_model.CpModel()
    #model = pulp.LpProblem("viptpp", pulp.LpMaximize)
    #model = Model("viptpp")

    all_stus = list(range(stu_cnt))
    all_days = list(range(weeks_cnt*7))[today_weeks_day:]
    all_class_slots = list(range(class_slot_cnt))
    all_teachers = list(range(tch_cnt))

    classvars_wtweight = {}
    d_stu_l_weight = collections.defaultdict(list)
    d_stu_weight_added = collections.defaultdict(int)
    for s in all_stus:
        tuple_stu = a_tuple_stu[s]
        for d in all_days:
            for cs in all_class_slots:
                if not cs_valid(d, today_weeks_day, cs, cal_start_slot):
                    continue
                for t in all_teachers:
                    if d_tuple_tch_slot.get((d, cs, t)) is None:
                        continue
                    class_var = model.NewBoolVar('class_s%i_d%i_cs%i_t%i' % (s, d, cs, t))
                    #class_var = pulp.LpVariable('class_s%i_d%i_cs%i_t%i' % (s, d, cs, t), lowBound=0, upBound=1, cat=pulp.LpInteger)
                    #class_var = model.addVar(vtype="B", name='class_s%i_d%i_cs%i_t%i' % (s, d, cs, t))
                    weight = 0
                    weight += tuple_stu.quit_value + \
                              tuple_stu.rebuy_value + \
                              ((1 if d % 7 == tuple_stu.most_week_day else 0) +
                              (1 if cs == tuple_stu.most_slot else 0)) * bonus_stu
                    for myt in range(tchcnt_stu):
                        weight += tchcnt_stu - myt if t == tuple_stu.l_teacher[myt] else 0
                    d_stu_l_weight[s].append(weight)
                    classvars_wtweight[(s, d, cs, t)] = (class_var, weight)
        if len(d_stu_l_weight[s]) > 0:
            d_stu_l_weight[s].sort(reverse=True)
            d_stu_weight_added[s] = sum(d_stu_l_weight[s][:tuple_stu.classes_per_week * weeks_cnt])

    for d in all_days:
        for cs in all_class_slots:
            if not cs_valid(d, today_weeks_day, cs, cal_start_slot):
                continue
            for t in all_teachers:
                if d_tuple_tch_slot.get((d, cs, t)) is None:
                    continue
                model.Add(sum(classvars_wtweight[(s, d, cs, t)][0] for s in all_stus) <= 1)
                #model += (sum(classvars_wtweight[(s, d, cs, t)][0] for s in all_stus) <= 1)
                #model.addCons(quicksum(classvars_wtweight[(s, d, cs, t)][0] for s in all_stus) <= 1)

    for s in all_stus:
        for d in all_days:
            for cs in all_class_slots:
                if not cs_valid(d, today_weeks_day, cs, cal_start_slot):
                    continue
                filtered_all_teachers = list(filter(lambda t:d_tuple_tch_slot.get((d, cs, t)) is not None, all_teachers))
                model.Add(sum(classvars_wtweight[(s, d, cs, t)][0] for t in filtered_all_teachers) <= a_tuple_stu[s].classes_per_week * weeks_cnt)
                #model += (sum(classvars_wtweight[(s, d, cs, t)][0] for t in filtered_all_teachers) <= a_tuple_stu[s].classes_per_week * weeks_cnt)
                #model.addCons(quicksum(classvars_wtweight[(s, d, cs, t)][0] for t in filtered_all_teachers) <= a_tuple_stu[s].classes_per_week * weeks_cnt)

    # Gain objective.
    #max_var_value = sum(v_classvar_wtweight[1] for v_classvar_wtweight in classvars_wtweight.values())
    max_var_value = sum(d_stu_weight_added.values())
    mylogger.info('max_var_value:{}'.format(max_var_value))
    obj_var =  model.NewIntVar(0, max_var_value, 'obj_var')
    model.Add(obj_var == sum(v_classvar_wtweight[0] * v_classvar_wtweight[1] for v_classvar_wtweight in classvars_wtweight.values()))
    model.Maximize(obj_var)
    #model += sum(v_classvar_wtweight[0] * v_classvar_wtweight[1] for v_classvar_wtweight in classvars_wtweight.values())
    #model.setObjective(sum(v_classvar_wtweight[0] * v_classvar_wtweight[1] for v_classvar_wtweight in classvars_wtweight.values()), sense="maximize")

    # Solve model.
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    '''
    model.solve()
    status = pulp.LpStatus[model.status]
    '''
    mylogger.info('status:{}'.format(status))
    '''
    model.optimize()
    print("\ngap:{}".format(model.getGap()))
    '''

    assigned_class_type = collections.namedtuple('assigned_class_type',
                                                'day_classslot student weeksday classslot')
    #if status == cp_model.OPTIMAL:
    print('User time: %.2fs' % solver.UserTime())
    print('Wall time: %.2fs' % solver.WallTime())
    print('Optimal gain value: %i' % solver.ObjectiveValue())
    #print('Optimal gain value: %i' % pulp.value(model.objective))
    '''
    print(model.getBestSol())
    '''

    # Create one list of assigned tasks per teacher.
    assigned_classes = collections.defaultdict(list)
    for t in all_teachers:
        for s in all_stus:
            for d in all_days:
                for cs in all_class_slots:
                    if not cs_valid(d, today_weeks_day, cs, cal_start_slot):
                        continue
                    if d_tuple_tch_slot.get((d, cs, t)) is None:
                        continue
                    class_var = classvars_wtweight[(s, d, cs, t)][0]
                    b_scheduled = solver.Value(class_var)
                    #b_scheduled = model.variablesDict()['class_s%i_d%i_cs%i_t%i' % (s, d, cs, t)]
                    #b_scheduled = bool(model.getVal(class_var))
                    if b_scheduled:
                    #if b_scheduled == 1:
                    #if b_scheduled:
                        assigned_classes[t].append(assigned_class_type(
                                day_classslot=d * 48 + cs,
                                student=s,
                                weeksday=d,
                                classslot=cs))
        # Sort by day_classslot.
        assigned_classes[t].sort()

    # Draw GanttChart
    df = []
    for teacher in all_teachers:
        for assigned_class in assigned_classes[teacher]:
            week = int(assigned_class.weeksday/7)
            week_day = assigned_class.weeksday%7
            delta_days = week * 7 + week_day - today_weeks_day
            start = delta_days * 24 * 3600 + (assigned_class.classslot + class_slot_start_hour * 2) * 30 * 60
            duration = 30 * 60
            df.append(dict(Task="Tch%s" % (teacher+1), Start=cal_start_date + time_delta(0, start),
                           Finish=cal_start_date + time_delta(0, start + duration),
                           Resource="%s" % (assigned_class.student + 1), complete=assigned_class.student + 1))
    colors = {}
    for i in all_stus:
        key = "%s" % (i + 1)
        colors[key] = "rgb(%s, %s, %s)" % (rgb(), rgb(), rgb())
    fig = ff.create_gantt(df, colors=colors, index_col='Resource', group_tasks=True, show_colorbar=True)
    pyplt(fig, filename=r"./GanttChart_%s_%i.html" % (opt, mul), auto_open=False)
    mylogger.info('gantt end')

#file_name_suffix = input("Input config/student/teacher file name suffix: ")
file_name_suffix = '_stu32tch2_stuliketch2bonus3_tch2weekcn3'
data_cfg, check_cfg = load_text(data_path + 'cfg' + file_name_suffix + '.txt')
data_stu, check_stu = load_text(data_path + 'stu' + file_name_suffix + '.txt')
data_tch, check_tch = load_text(data_path + 'tch' + file_name_suffix + '.txt')
if data_cfg is not None and data_stu is not None and data_tch is not None:
    TimeTableOpt(data_cfg, data_stu, data_tch)
