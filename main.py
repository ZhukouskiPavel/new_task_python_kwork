'''
Здесь мы используем функцию `solve_lp`, которая решает линейную оптимизационную задачу для
каждого из частей базы данных, определяемых списком `employee_ids`. Мы используем библиотеку
 `multiprocessing` для запуска нескольких процессов параллельно, каждый из которых выполняет
 свою часть задачи.

В функции `solve_lp` мы определяем переменные, целевую функцию и ограничения,
 используя данные из базы данных. Затем мы решаем задачу линейного программирования
  с помощью метода `pulp.PULP_CBC_CMD` и возвращаем значение целевой функции.

В функции `main` мы определяем список `employee_ids`,
 используя базу данных, и разбиваем его на несколько частей,
  чтобы каждый процесс мог решить задачу линейного программирования для своей части.
   Затем мы запускаем несколько процессов параллельно, используя функцию `map` библиотеки `multiprocessing`,
    и суммируем значения целевой функции, возвращаемые каждым процессом. Наконец, мы выводим оптимальное значение
     целевой функции и время выполнения.

Некоторые комментарии к коду:

- Мы используем SQLite для базы данных, потому что он легко устанавливается и не требует дополнительных настроек.
 Однако, для больших объемов данных, возможно, потребуется более мощная база данных, такая как PostgreSQL или MySQL.

- Мы используем библиотеку PuLP для определения и решения задачи линейного программирования.
 PuLP поддерживает несколько солверов, но мы выбрали CBC (Coin-or branch and cut),
  который является открытым и бесплатным.

- Мы используем библиотеку multiprocessing для запуска нескольких процессов параллельно.
 При использовании нескольких процессов важно убедиться, что каждый процесс работает со своей собственной
  копией данных и не взаимодействует с другими процессами напрямую. В нашем случае мы разбиваем список `employee_ids`
  на части, чтобы каждый процесс работал с своей частью данных.

- Мы измеряем время выполнения с помощью функции `time.time()`.
'''

import time  # модуль для измерения времени выполнения
import sqlite3  # модуль для работы с базами данных SQLite
import pulp  # библиотека для решения линейных программ
from multiprocessing import Pool  # класс для реализации параллельных вычислений

'''при первом запуске скрипта!!! запустить эту функцию generate_data()  для заполнения таблицы в main()'''
from generate_data import generate_data

import warnings  # игнорировать предупреждения, на выполнение не влияет, предупреждает о пробелах

warnings.filterwarnings("ignore", message="Spaces are not permitted in the name.")


def solve_lp(chunk):
    # Создание объекта задачи оптимизации
    prob = pulp.LpProblem("LP Problem", pulp.LpMaximize)

    # Определение целевой функции
    x = []
    for i in chunk:
        var_name = f"x{i}"
        var = pulp.LpVariable(var_name, lowBound=0, cat="Continuous")
        x.append(var)

    # Определение целевой функции
    obj = []
    for i in range(len(chunk)):
        obj.append(x[i])
    prob += pulp.lpSum(obj)

    conn = sqlite3.connect('company.db')
    c = conn.cursor()
    # Извлечение зарплат из базы данных SQLite для сотрудников, входящих в текущий набор
    c.execute("SELECT salary FROM employees WHERE id IN ({seq})".format(seq=','.join(['?'] * len(chunk))), chunk)
    salaries = c.fetchall()
    conn.close()
    # Добавление ограничений на зарплаты
    for i in range(len(chunk)):
        prob += x[i] <= salaries[i][0]
    # Решение линейной программы
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    # Возврат значения целевой функции для данного набора сотрудников
    return pulp.value(prob.objective)


def main():
    # Извлечение идентификаторов всех сотрудников из базы данных SQLite
    conn = sqlite3.connect('company.db')
    c = conn.cursor()
    c.execute("SELECT id FROM employees")
    employee_ids = [row[0] for row in c.fetchall()]
    conn.close()

    # Sequential LP Решение линейной программы последовательно
    start_time_seq = time.time()
    obj_value_seq = solve_lp(employee_ids)
    end_time_seq = time.time()
    print(f"Optimal objective value (sequential): {obj_value_seq}")
    print(f"Execution time (sequential): {end_time_seq - start_time_seq} seconds")

    # Parallel LP Решение линейной программы параллельно
    num_workers = 4
    chunk_size = len(employee_ids) // num_workers
    chunks = [employee_ids[i:i + chunk_size] for i in range(0, len(employee_ids), chunk_size)]
    start_time_par = time.time()
    with Pool(num_workers) as p:
        results = p.map(solve_lp, chunks)
    end_time_par = time.time()
    print(f"Optimal objective value (parallel): {sum(results)}")
    print(f"Execution time (parallel): {end_time_par - start_time_par} seconds")


if __name__ == "__main__":
    main()
