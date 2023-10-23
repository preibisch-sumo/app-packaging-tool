import yaml


class Author:
    def __init__(self, name, supportUrl, homeUrl, documentationUrl):
        self.name = name
        self.supportUrl = supportUrl
        self.homeUrl = homeUrl
        self.documentationUrl = documentationUrl

    def __str__(self):
        return f"Name: {self.name}, Support URL: {self.supportUrl}, Home URL: {self.homeUrl}, Documentation URL: {self.documentationUrl}"


class AppOverview:
    def __init__(self, overview, setup, metrics, troubleshooting):
        self.overview = overview
        self.setup = setup
        self.metrics = metrics
        self.troubleshooting = troubleshooting

    def __str__(self):
        return f"Overview: {self.overview}, Setup: {self.setup}, Metrics: {self.metrics}, Troubleshooting: {self.troubleshooting}"


class AppMedia:
    def __init__(self, title, description, media_type, location):
        self.title = title
        self.description = description
        self.type = media_type
        self.location = location

    def __str__(self):
        return f"Title: {self.title}, Description: {self.description}, Type: {self.type}, Location: {self.location}"


class Manifest:
    def __init__(self, yaml_file_path):
        with open(yaml_file_path, 'r') as f:
            data = yaml.safe_load(f)

        self.schemaVersion = data.get('schemaVersion', None)
        self.name = data.get('name', None)
        self.version = data.get('version', None)
        self.description = data.get('description', None)

        author_data = data.get('author', {})
        self.author = Author(author_data.get('name', None),
                             author_data.get('supportUrl', None),
                             author_data.get('homeUrl', None),
                             author_data.get('documentationUrl', None))

        overview_data = data.get('appOverview', {})
        self.appOverview = AppOverview(overview_data.get('overview', None),
                                       overview_data.get('setup', None),
                                       overview_data.get('metrics', None),
                                       overview_data.get('troubleshooting', None))

        self.attributes = data.get('attributes', {})
        self.accountTypes = data.get('accountTypes', [])

        media_data = data.get('appMedia', [])
        self.appMedia = [AppMedia(media.get('title', None),
                                  media.get('description', None),
                                  media.get('type', None),
                                  media.get('location', None)) for media in media_data]

        self.family = data.get('family', None)
        self.installable = data.get('installable', None)
        self.showOnMarketplace = data.get('showOnMarketplace', None)

    def __str__(self):
        return (f"Schema Version: {self.schemaVersion}\n"
                f"Name: {self.name}\n"
                f"Version: {self.version}\n"
                f"Description: {self.description}\n"
                f"Author: {self.author}\n"
                f"Attributes: {self.attributes}\n"
                f"Account Types: {self.accountTypes}\n"
                f"App Overview: {self.appOverview}\n"
                f"App Media: {[str(media) for media in self.appMedia]}\n"
                f"Family: {self.family}\n"
                f"Installable: {self.installable}\n"
                f"Show on Marketplace: {self.showOnMarketplace}")
