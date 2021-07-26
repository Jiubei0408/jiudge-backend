import os.path

from flask import make_response, send_file


def next_problem_id(problem_id: str):
    """
    求下一个问题编号
    :param problem_id: 当前问题标号
    :return: 下一个问题标号
    """
    problem_id = list(problem_id[::-1])
    index = 0
    l = len(problem_id)
    while index < l:
        if problem_id[index] < 'Z':
            problem_id[index] = chr(ord(problem_id[index]) + 1)
            return ''.join(problem_id)[::-1]
        problem_id[index] = 'A'
        index += 1
    problem_id.append('A')
    return ''.join(problem_id)[::-1]


def save_to_file(data, filename, filedir=''):
    import os
    filedir = 'files' + filedir
    if not os.path.exists(filedir):
        os.makedirs(filedir)
    filename = f'{filedir}/{filename}'
    open_type = 'wb'
    if type(data) == 'str':
        open_type = 'w'
    with open(filename, open_type) as f:
        f.write(data)
    return filename


def get_file_response(loc):
    return make_response(send_file(os.path.abspath(loc)))
