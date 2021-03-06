import argparse

from .base import BaseResourceManager
from .repositories import RepositoryManager
from cliff.command import Command
from cliff.show import ShowOne
from cliff.lister import Lister

class Source(object):
    @property
    def builds(self):
        return self.client.Builds.list(self.builds_url)


class SourceManager(BaseResourceManager):
    object_class = Source
    path = '/sources/'

    def from_json(self, data):
        obj = self.object_class()
        obj.client = self.client
        obj.self = data['self']
        obj.git_url = data['git_repository']
        obj.git_branch = data['git_branch']
        obj.repository = self.client.Repositories.get(url=data['repository'], cached=True)
        obj.builds_url = data['builds']
        return obj


class SourceLister(Lister):
    def format_sources(self, sources):
        data = []

        for source in sources:
            data.append((source.self, source.git_url, source.git_branch,
                         '%s/%s' % (source.repository.user, source.repository.name)))

        return (('Id', 'Git url', 'Git branch', 'APT repository'), data)

class Delete(Command):
    """ Delete source """

    def get_parser(self, prog_name):
        parser = super(Delete, self).get_parser(prog_name)
        parser.add_argument('id', metavar='ID')
        return parser

    def take_action(self, parsed_args):
        if self.app.client.Sources.delete(parsed_args.id):
            print 'Deleted'
        else:
            print 'Not deleted. Perhaps it did not exist?'


class Create(ShowOne):
    """ Create source """

    def get_parser(self, prog_name):
        parser = super(Create, self).get_parser(prog_name)
        parser.add_argument('url')
        parser.add_argument('branch')
        parser.add_argument('repository')
        return parser


    def take_action(self, parsed_args):
        source = self.app.client.Sources.create(git_repository=parsed_args.url,
                                                git_branch=parsed_args.branch,
                                                repository=parsed_args.repository)
        return (('Id', 'Git url', 'Git branch', 'APT repository'), (source.self, source.git_url, source.git_branch,
                         '%s/%s' % (source.repository.user, source.repository.name)))


class List(SourceLister):
    """ List all sources """

    def take_action(self, parsed_args):
        # Warm the cache
        list(self.app.client.Repositories.list())

        return self.format_sources(self.app.client.Sources.list())


class ListByRepository(SourceLister):
    """ List all sources for given repository """

    def get_parser(self, prog_name):
        parser = super(ListByRepository, self).get_parser(prog_name)
        parser.add_argument('id')
        return parser


    def take_action(self, parsed_args):
        repository = self.app.client.Repositories.get(parsed_args.id)
        return self.format_sources(repository.sources)
