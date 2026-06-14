"""GitHub projects list for /projects page."""

from __future__ import annotations

from app.core import projects as projects_mod


def test_list_github_projects_excludes_aimsync(monkeypatch):
    sample = [
        {
            'name': 'KryptAim',
            'full_name': 'AimSyncCore/KryptAim',
            'description': 'Current app',
            'html_url': 'https://github.com/AimSyncCore/KryptAim',
            'stargazers_count': 10,
            'language': 'Python',
            'updated_at': '2026-01-01T00:00:00Z',
            'topics': [],
            'fork': False,
        },
        {
            'name': 'Other',
            'full_name': 'AimSyncCore/Other',
            'description': 'Side project',
            'html_url': 'https://github.com/AimSyncCore/Other',
            'stargazers_count': 1,
            'language': 'TypeScript',
            'updated_at': '2026-01-02T00:00:00Z',
            'topics': [],
            'fork': False,
        },
    ]

    monkeypatch.setattr(projects_mod, '_repo_items', lambda _t, _n: sample)
    projects_mod._CACHE['at'] = 0.0
    projects_mod._CACHE['projects'] = []

    names = [p['name'] for p in projects_mod.list_github_projects(refresh=True)['projects']]
    assert 'KryptAim' not in names
    assert 'Other' in names


def test_featured_projects_use_curated_copy(monkeypatch):
    sample = [{
        'name': 'cs2_webradar',
        'full_name': 'AimSyncCore/cs2_webradar',
        'description': 'Short GitHub blurb',
        'html_url': 'https://github.com/AimSyncCore/cs2_webradar',
        'stargazers_count': 1,
        'language': 'C++',
        'updated_at': '2026-06-01T00:00:00Z',
        'topics': [],
        'fork': False,
    }]

    monkeypatch.setattr(projects_mod, '_repo_items', lambda _t, _n: sample)
    monkeypatch.setattr(projects_mod, '_load_config', lambda: {
        'featured': [{
            'repo': 'AimSyncCore/cs2_webradar',
            'name': 'KryptAim WebRadar',
            'description': 'Live CS2 web radar with 44 maps.',
            'order': 1,
            'tags': ['CS2'],
        }],
        'sources': [{'type': 'org', 'name': 'AimSyncCore'}],
        'exclude_repos': ['KryptAim'],
        'exclude_forks': True,
    })
    projects_mod._CACHE['at'] = 0.0
    projects_mod._CACHE['projects'] = []

    projects = projects_mod.list_github_projects(refresh=True)['projects']
    assert projects[0]['name'] == 'KryptAim WebRadar'
    assert '44 maps' in projects[0]['description']
    assert projects[0]['featured'] is True
