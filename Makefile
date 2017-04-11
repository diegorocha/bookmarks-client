test:
	@coverage run --source=bookmarks_client manage.py test
	@coverage html --omit=*/migrations/*,*/wsgi.py,*/tests.py,*/apps.py,*/settings.py -d coverage
