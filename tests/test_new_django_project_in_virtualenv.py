from unittest.mock import patch, call
import getpass
import os
import pytest
import subprocess

from new_django_project_in_virtualenv import (
    create_virtualenv,
    create_webapp,
    main,
    start_django_project,
)


@patch('new_django_project_in_virtualenv.create_virtualenv')
@patch('new_django_project_in_virtualenv.start_django_project')
@patch('new_django_project_in_virtualenv.create_webapp')
class TestMain:

    def test_calls_create_virtualenv(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        main('domain', 'django.version', 'python.version')
        assert mock_create_virtualenv.call_args == call(
            'domain', 'python.version', 'django.version'
        )


    def test_domain_defaults_to_using_current_username(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        username = getpass.getuser()
        main('your-username.pythonanywhere.com', 'django.version', 'python.version')
        assert mock_create_virtualenv.call_args == call(
            username + '.pythonanywhere.com', 'python.version', 'django.version'
        )


    def test_calls_start_django_project_with_virtualenv(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        main('domain', 'django.version', 'python.version')
        assert mock_start_django_project.call_args == call(
            'domain', mock_create_virtualenv.return_value
        )


    def test_calls_create_webapp_with_virtualenv_and_python_version(
        self, mock_create_webapp, mock_start_django_project,
        mock_create_virtualenv
    ):
        main('domain', 'django.version', 'python.version')
        assert mock_create_webapp.call_args == call(
            'domain', 'python.version', mock_create_virtualenv.return_value, mock_start_django_project.return_value
        )


class TestCreateVirtualenv:

    @patch('new_django_project_in_virtualenv.subprocess')
    def test_uses_bash_and_sources_virtualenvwrapper(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'latest')
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[:2] == ['bash', '-c']
        assert command_list[2].startswith('source virtualenvwrapper.sh && mkvirtualenv')


    @patch('new_django_project_in_virtualenv.subprocess')
    def test_calls_mkvirtualenv_with_python_version_and_domain(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'latest')
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        bash_command = command_list[2]
        assert 'mkvirtualenv --python=/usr/bin/python2.7 domain.com' in bash_command


    @patch('new_django_project_in_virtualenv.subprocess')
    def test_django_version_for_latest(self, mock_subprocess):
        create_virtualenv('domain.com', '2.7', 'latest')
        args, kwargs = mock_subprocess.check_call.call_args
        command_list = args[0]
        assert command_list[2].endswith('pip install django')


    @pytest.mark.slowtest
    def test_actually_creates_a_virtualenv_with_right_django_version_in(self, virtualenvs_folder):
        domain = 'mydomain.com'
        create_virtualenv(domain, '2.7', '1.9')

        assert domain in os.listdir(virtualenvs_folder)
        django_version = subprocess.check_output([
            os.path.join(virtualenvs_folder, domain, 'bin/python'),
            '-c'
            'import django; print(django.get_version())'
        ]).decode().strip()
        assert django_version == '1.9'


class TestStartDjangoProject:

    @pytest.mark.slowtest
    def test_actually_creates_a_django_project(self, test_virtualenv, fake_home):
        home = os.path.expanduser('~')
        start_django_project('mydomain.com', test_virtualenv)
        assert 'mydomain.com' in os.listdir(home)
        assert 'settings.py' in os.listdir(os.path.join(home, 'mydomain.com', 'mysite'))

