
def detect_key_moments(events):
    score = {"HOME": 0, "AWAY": 0}
    moments = []

    for event in events:
        if event["event_type"] != "shot" or event["outcome"] != "goal":
            continue

        team = event["team_id"]
        opponent = "AWAY" if team == "HOME" else "HOME"

        previous_difference = score[team] - score[opponent]
        score[team] += 1
        new_difference = score[team] - score[opponent]

        if new_difference == 0:
            significance = "equaliser"
        elif previous_difference <= 0 and new_difference > 0:
            significance = "takes_lead"
        else:
            significance = "extends_lead"

        moments.append({
            "minute": event["minute"],
            "team_id": team,
            "player_name": event.get("player_name"),
            "event_type": "goal",
            "significance": significance,
            "score": score.copy()
        })

    return moments


def identify_winning_goal(moments):
    if not moments:
        return moments

    final_score = moments[-1]["score"]
    home_goals = final_score["HOME"]
    away_goals = final_score["AWAY"]

    if home_goals == away_goals:
        return moments

    winner = "HOME" if home_goals > away_goals else "AWAY"
    loser = "AWAY" if winner == "HOME" else "HOME"

    for moment in moments:
        score = moment["score"]

        if (
            moment["team_id"] == winner
            and score[winner] > final_score[loser]
        ):
            moment["is_winning_goal"] = True
            break

    return moments
