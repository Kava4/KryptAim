"""Map CS2 team side (CT/T) to enemy model class labels."""

from __future__ import annotations


def find_class_label(labels: list[str], token: str) -> str:
    token_u = token.strip().upper()
    if not token_u:
        return ''
    for label in labels:
        if label.strip().upper() == token_u:
            return label
    for label in labels:
        upper = label.strip().upper()
        if token_u == 'CT' and (upper == 'CT' or upper.startswith('COUNTER')):
            return label
        if token_u == 'T' and upper == 'T':
            return label
        if token_u == 'T' and upper.startswith('T') and not upper.startswith('CT'):
            return label
    return ''


def enemy_token_for_team(my_team: str) -> str:
    team = my_team.strip().lower()
    if team == 'ct':
        return 'T'
    if team == 't':
        return 'CT'
    return ''


def enemy_class_for_team(my_team: str, labels: list[str]) -> str:
    return find_class_label(labels, enemy_token_for_team(my_team))


def has_ct_t_classes(labels: list[str]) -> bool:
    return bool(find_class_label(labels, 'CT')) and bool(find_class_label(labels, 'T'))
