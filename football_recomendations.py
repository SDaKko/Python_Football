from flask import Flask, render_template, request
import rdflib
from urllib.parse import urlparse

app = Flask(__name__, template_folder='templates')

# Загрузка онтологии
graph = rdflib.Graph()
graph.parse("football_eng.ttl", format="turtle")

namespaces = {
    "ex": "http://example.org/football-ise/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#"
}


def get_label(uri):
    """Получить читаемую метку для URI"""
    if not uri:
        return ""

    # Пробуем получить метку из онтологии
    label_query = f"""
    SELECT ?label
    WHERE {{
        <{uri}> rdfs:label ?label .
        FILTER(LANG(?label) = "" || LANGMATCHES(LANG(?label), "ru"))
    }}
    LIMIT 1
    """

    try:
        qres = graph.query(label_query, initNs=namespaces)
        for row in qres:
            return str(row["label"])
    except:
        pass

    # Если метки нет, извлекаем имя из URI
    parsed = urlparse(uri)
    if parsed.fragment:
        return parsed.fragment
    else:
        return uri.split('/')[-1]


def filter_results(results, filters):
    """Фильтровать результаты по заданным критериям"""
    if not filters:
        return results

    filtered_results = []
    for result in results:
        match = True
        for key, value in filters.items():
            if value:  # Если фильтр указан
                if key in result:
                    # Преобразуем оба значения к нижнему регистру для поиска
                    filter_value = str(value).lower()
                    result_value = str(result[key]).lower()
                    if filter_value not in result_value:
                        match = False
                        break
                else:
                    match = False
                    break
        if match:
            filtered_results.append(result)

    return filtered_results


def analyze_decisions_by_context():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?context ?decision ?action ?decisionTime ?scoreDiff ?matchMinute
    WHERE {
      ?context a ex:Context ;
               ex:influences ?decision ;
               ex:scoreDiff ?scoreDiff ;
               ex:matchMinute ?matchMinute .
      ?decision a ex:Decision ;
                ex:chosenOption ?action ;
                ex:decisionTime ?decisionTime .
    }
    ORDER BY ?matchMinute
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "context": get_label(str(row["context"])),
            "context_uri": str(row["context"]),
            "decision": get_label(str(row["decision"])),
            "decision_uri": str(row["decision"]),
            "action": get_label(str(row["action"])),
            "action_uri": str(row["action"]),
            "decisionTime": float(row["decisionTime"]),
            "scoreDiff": int(row["scoreDiff"]),
            "matchMinute": int(row["matchMinute"])
        })
    return results


def evaluate_action_effectiveness():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?actionType (COUNT(?decision) as ?usageCount) 
           (AVG(?successProb) as ?avgSuccessProbability)
           (AVG(?expectedValue) as ?avgExpectedValue)
    WHERE {
      ?decision ex:chosenOption ?action .
      ?action ex:hasActionType ?actionType .
      ?eval ex:considersOptions ?action ;
            ex:optionSuccessProbability ?successProb ;
            ex:expectedValue ?expectedValue .
    }
    GROUP BY ?actionType
    ORDER BY DESC(?avgExpectedValue)
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "actionType": get_label(str(row["actionType"])),
            "actionType_uri": str(row["actionType"]),
            "usageCount": int(row["usageCount"]),
            "avgSuccessProbability": float(row["avgSuccessProbability"]),
            "avgExpectedValue": float(row["avgExpectedValue"])
        })
    return results


def analyze_pressure_influence():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?pressureLevel ?zone 
           (COUNT(?decision) as ?decisionCount)
           (AVG(?decisionTime) as ?avgDecisionTime)
           (AVG(?timePressure) as ?avgTimePressure)
    WHERE {
      ?situation ex:occursInZone ?zone ;
                 ex:isCharacterizedBy ?eval .
      ?eval ex:considersPressure ?pressureLevel ;
            ex:timePressure ?timePressure .
      ?decision ex:basedOnEvaluation ?eval ;
                ex:decisionTime ?decisionTime .
    }
    GROUP BY ?pressureLevel ?zone
    ORDER BY ?pressureLevel ?zone
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "pressureLevel": get_label(str(row["pressureLevel"])),
            "pressureLevel_uri": str(row["pressureLevel"]),
            "zone": get_label(str(row["zone"])),
            "zone_uri": str(row["zone"]),
            "decisionCount": int(row["decisionCount"]),
            "avgDecisionTime": float(row["avgDecisionTime"]),
            "avgTimePressure": float(row["avgTimePressure"])
        })
    return results


def analyze_coaching_influence():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?coachingInstruction ?decision ?action ?phase ?zone
    WHERE {
      ?coachingInstruction a ex:CoachInstructions ;
                           ex:influence ?decision .
      ?decision ex:chosenOption ?action .
      ?situation ex:isCharacterizedBy ?eval ;
                 ex:hasPhase ?phase ;
                 ex:occursInZone ?zone .
      ?decision ex:basedOnEvaluation ?eval .
    }
    ORDER BY ?coachingInstruction
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "coachingInstruction": get_label(str(row["coachingInstruction"])),
            "coachingInstruction_uri": str(row["coachingInstruction"]),
            "decision": get_label(str(row["decision"])),
            "decision_uri": str(row["decision"]),
            "action": get_label(str(row["action"])),
            "action_uri": str(row["action"]),
            "phase": get_label(str(row["phase"])),
            "phase_uri": str(row["phase"]),
            "zone": get_label(str(row["zone"])),
            "zone_uri": str(row["zone"])
        })
    return results


def analyze_constraints():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?constraint ?constraintType ?severity ?action
    WHERE {
      ?constraint a ex:Constraint ;
                  ex:hasConstraintType ?constraintType ;
                  ex:constraintSeverity ?severity .
      ?action ex:limitedBy ?constraint .
    }
    GROUP BY ?constraint ?constraintType ?severity ?action
    ORDER BY DESC(?severity)
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "constraint": get_label(str(row["constraint"])),
            "constraint_uri": str(row["constraint"]),
            "constraintType": get_label(str(row["constraintType"])),
            "constraintType_uri": str(row["constraintType"]),
            "severity": float(row["severity"]),
            "action": get_label(str(row["action"])),
            "action_uri": str(row["action"])
        })
    return results


def spatial_analysis():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?zone ?spaceAvailability ?pressureLevel
           (COUNT(?situation) as ?situationCount)
           (AVG(?distanceToDefender) as ?avgDefenderDistance)
           (AVG(?angleToGoal) as ?avgGoalAngle)
    WHERE {
      ?situation ex:occursInZone ?zone ;
                 ex:isCharacterizedBy ?eval .
      ?eval ex:considersSpace ?spaceAvailability ;
            ex:considersPressure ?pressureLevel ;
            ex:distanceToNearestDefender ?distanceToDefender ;
            ex:angleToGoal ?angleToGoal .
    }
    GROUP BY ?zone ?spaceAvailability ?pressureLevel
    ORDER BY ?zone ?spaceAvailability
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "zone": get_label(str(row["zone"])),
            "zone_uri": str(row["zone"]),
            "spaceAvailability": get_label(str(row["spaceAvailability"])),
            "spaceAvailability_uri": str(row["spaceAvailability"]),
            "pressureLevel": get_label(str(row["pressureLevel"])),
            "pressureLevel_uri": str(row["pressureLevel"]),
            "situationCount": int(row["situationCount"]),
            "avgDefenderDistance": float(row["avgDefenderDistance"]),
            "avgGoalAngle": float(row["avgGoalAngle"])
        })
    return results


def analyze_observation_chain():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?situation ?eval ?decision ?execution ?outcome ?player
    WHERE {
      ?situation ex:isCharacterizedBy ?eval .
      ?decision ex:basedOnEvaluation ?eval ;
                ex:executes ?execution .
      ?execution ex:hasOutcome ?outcome .
      ?player ex:involvesPlayer ?situation . 
    }
    ORDER BY ?situation
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "situation": get_label(str(row["situation"])),
            "situation_uri": str(row["situation"]),
            "eval": get_label(str(row["eval"])),
            "eval_uri": str(row["eval"]),
            "decision": get_label(str(row["decision"])),
            "decision_uri": str(row["decision"]),
            "execution": get_label(str(row["execution"])),
            "execution_uri": str(row["execution"]),
            "outcome": get_label(str(row["outcome"])),
            "outcome_uri": str(row["outcome"]),
            "player": get_label(str(row["player"])),
            "player_uri": str(row["player"])
        })
    return results


def analyze_player_roles():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?player ?team 
           (COUNT(DISTINCT ?situation) as ?situationsInvolved)
           (COUNT(DISTINCT ?decision) as ?decisionsMade)
    WHERE {
      ?player a ex:Player ;
              ex:belongsToTeam ?team .
      OPTIONAL { ?player ex:involvesPlayer ?situation . }
      OPTIONAL { ?player ex:madeByPlayer ?decision. }
    }
    GROUP BY ?player ?team
    ORDER BY DESC(?situationsInvolved)
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "player": get_label(str(row["player"])),
            "player_uri": str(row["player"]),
            "team": get_label(str(row["team"])),
            "team_uri": str(row["team"]),
            "situationsInvolved": int(row["situationsInvolved"]),
            "decisionsMade": int(row["decisionsMade"])
        })
    return results


def analyze_phase_decisions():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?phase
           (COUNT(?decision) as ?decisionCount)
           (AVG(?decisionTime) as ?avgDecisionTime)
           (AVG(?timePressure) as ?avgTimePressure)
    WHERE {
      ?context ex:influences ?decision ;
               ex:matchMinute ?minute .
      ?decision ex:decisionTime ?decisionTime .
      ?situation ex:isCharacterizedBy ?eval ;
                 ex:hasPhase ?phase .
      ?eval ex:timePressure ?timePressure .
    }
    GROUP BY ?phase
    ORDER BY ?phase
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "phase": get_label(str(row["phase"])),
            "phase_uri": str(row["phase"]),
            "decisionCount": int(row["decisionCount"]),
            "avgDecisionTime": float(row["avgDecisionTime"]),
            "avgTimePressure": float(row["avgTimePressure"])
        })
    return results


def analyze_high_value_situations():
    query = """
    PREFIX ex: <http://example.org/football-ise/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?situation ?zone ?phase ?space ?pressure 
           ?expectedValue ?successProbability ?chosenAction
    WHERE {
      ?situation ex:occursInZone ?zone ;
                 ex:hasPhase ?phase ;
                 ex:isCharacterizedBy ?eval .
      ?eval ex:considersSpace ?space ;
            ex:considersPressure ?pressure ;
            ex:expectedValue ?expectedValue ;
            ex:optionSuccessProbability ?successProbability .
      ?decision ex:basedOnEvaluation ?eval ;
                ex:chosenOption ?chosenAction .
      FILTER (?expectedValue > 0.3)
    }
    ORDER BY DESC(?expectedValue)
    """

    qres = graph.query(query, initNs=namespaces)
    results = []
    for row in qres:
        results.append({
            "situation": get_label(str(row["situation"])),
            "situation_uri": str(row["situation"]),
            "zone": get_label(str(row["zone"])),
            "zone_uri": str(row["zone"]),
            "phase": get_label(str(row["phase"])),
            "phase_uri": str(row["phase"]),
            "space": get_label(str(row["space"])),
            "space_uri": str(row["space"]),
            "pressure": get_label(str(row["pressure"])),
            "pressure_uri": str(row["pressure"]),
            "expectedValue": float(row["expectedValue"]),
            "successProbability": float(row["successProbability"]),
            "chosenAction": get_label(str(row["chosenAction"])),
            "chosenAction_uri": str(row["chosenAction"])
        })
    return results


# Словари для конфигурации запросов
QUERY_CONFIGS = {
    'decisions_by_context': {
        'title': 'Анализ решений по контексту матча',
        'headers': ['Контекст', 'Решение', 'Действие', 'Время решения (сек)', 'Разница в счёте', 'Минута матча'],
        'keys': ['context', 'decision', 'action', 'decisionTime', 'scoreDiff', 'matchMinute'],
        'filter_fields': ['context', 'decision', 'action'],
        'function': analyze_decisions_by_context
    },
    'action_effectiveness': {
        'title': 'Эффективность различных типов действий',
        'headers': ['Тип действия', 'Количество использований', 'Средняя вероятность успеха',
                    'Среднее ожидаемое значение'],
        'keys': ['actionType', 'usageCount', 'avgSuccessProbability', 'avgExpectedValue'],
        'filter_fields': ['actionType'],
        'function': evaluate_action_effectiveness
    },
    'pressure_analysis': {
        'title': 'Влияние давления на принятие решений',
        'headers': ['Уровень давления', 'Зона', 'Количество решений', 'Среднее время решения (сек)',
                    'Среднее временное давление'],
        'keys': ['pressureLevel', 'zone', 'decisionCount', 'avgDecisionTime', 'avgTimePressure'],
        'filter_fields': ['pressureLevel', 'zone'],
        'function': analyze_pressure_influence
    },
    'coaching_influence': {
        'title': 'Влияние установок тренера',
        'headers': ['Установка тренера', 'Решение', 'Действие', 'Фаза игры', 'Зона'],
        'keys': ['coachingInstruction', 'decision', 'action', 'phase', 'zone'],
        'filter_fields': ['coachingInstruction', 'decision', 'action', 'phase', 'zone'],
        'function': analyze_coaching_influence
    },
    'constraints': {
        'title': 'Ограничения и их влияние на варианты действий',
        'headers': ['Ограничение', 'Тип ограничения', 'Степень влияния', 'Действие'],
        'keys': ['constraint', 'constraintType', 'severity', 'action'],
        'filter_fields': ['constraint', 'constraintType', 'action'],
        'function': analyze_constraints
    },
    'spatial_analysis': {
        'title': 'Пространственный анализ ситуаций',
        'headers': ['Зона', 'Доступное пространство', 'Уровень давления', 'Количество ситуаций',
                    'Ср. дистанция до защитника (м)', 'Ср. угол к воротам'],
        'keys': ['zone', 'spaceAvailability', 'pressureLevel', 'situationCount', 'avgDefenderDistance', 'avgGoalAngle'],
        'filter_fields': ['zone', 'spaceAvailability', 'pressureLevel'],
        'function': spatial_analysis
    },
    'observation_chain': {
        'title': 'Цепочка "Наблюдение → Оценка → Решение → Исполнение → Исход"',
        'headers': ['Ситуация', 'Оценка', 'Решение', 'Исполнение', 'Исход', 'Игрок'],
        'keys': ['situation', 'eval', 'decision', 'execution', 'outcome', 'player'],
        'filter_fields': ['situation', 'decision', 'outcome', 'player'],
        'function': analyze_observation_chain
    },
    'player_roles': {
        'title': 'Анализ игроков и их ролей в различных ситуациях',
        'headers': ['Игрок', 'Команда', 'Участие в ситуациях', 'Принятые решения'],
        'keys': ['player', 'team', 'situationsInvolved', 'decisionsMade'],
        'filter_fields': ['player', 'team'],
        'function': analyze_player_roles
    },
    'phase_analysis': {
        'title': 'Анализ принятых решений в различных фазах',
        'headers': ['Фаза игры', 'Количество решений', 'Среднее время решения (сек)', 'Среднее временное давление'],
        'keys': ['phase', 'decisionCount', 'avgDecisionTime', 'avgTimePressure'],
        'filter_fields': ['phase'],
        'function': analyze_phase_decisions
    },
    'high_value_situations': {
        'title': 'Анализ ситуаций с высоким ожидаемым значением',
        'headers': ['Ситуация', 'Зона', 'Фаза', 'Пространство', 'Давление', 'Ожидаемое значение', 'Вероятность успеха',
                    'Выбранное действие'],
        'keys': ['situation', 'zone', 'phase', 'space', 'pressure', 'expectedValue', 'successProbability',
                 'chosenAction'],
        'filter_fields': ['situation', 'zone', 'phase', 'space', 'pressure', 'chosenAction'],
        'function': analyze_high_value_situations
    }
}


@app.route('/')
def index():
    return render_template('index.html')


# Маршруты для каждого запроса
@app.route('/<query_name>', methods=['GET', 'POST'])
def display_query(query_name):
    if query_name not in QUERY_CONFIGS:
        return "Запрос не найден", 404

    config = QUERY_CONFIGS[query_name]

    # Получаем фильтры из формы
    filters = {}
    if request.method == 'POST':
        for field in config.get('filter_fields', []):
            filter_value = request.form.get(field, '').strip()
            if filter_value:
                filters[field] = filter_value

    # Получаем все результаты
    all_results = config['function']()

    # Применяем фильтры
    filtered_results = filter_results(all_results, filters)

    # Подготавливаем данные для отображения
    display_keys = config['keys']

    return render_template('table_template.html',
                           title=config['title'],
                           headers=config['headers'],
                           keys=display_keys,
                           results=filtered_results,
                           filter_fields=config.get('filter_fields', []),
                           current_filters=filters)


if __name__ == '__main__':
    app.run(debug=True)