

class RegistryItem(dict):
    @property
    def types(self) -> tuple:
        return tuple(self.values())


class Registry:
    _django = RegistryItem()
    _forms = RegistryItem()
    _pages = RegistryItem()
    _settings = RegistryItem()
    _snippets = RegistryItem()
    _snippets_by_name = RegistryItem()
    _streamfield_blocks = RegistryItem()
    _streamfield_scalar_blocks = RegistryItem()
    _page_prefetch = {
        'content_type', 'owner',
        'live_revision', 'page_ptr'
    }

    @property
    def blocks(self) -> RegistryItem:
        return self._streamfield_blocks

    @property
    def scalar_blocks(self) -> RegistryItem:
        return self._streamfield_scalar_blocks

    @property
    def django(self) -> RegistryItem:
        return self._django

    @property
    def forms(self) -> RegistryItem:
        return self._forms

    @property
    def pages(self) -> RegistryItem:
        return self._pages

    @property
    def settings(self) -> RegistryItem:
        return self._settings

    @property
    def snippets(self) -> RegistryItem:
        return self._snippets

    @property
    def snippets_by_name(self) -> RegistryItem:
        return self._snippets_by_name

    @property
    def rsnippets(self) -> RegistryItem:
        return RegistryItem((v, k) for k, v in self._snippets.items())

    @property
    def page_prefetch_fields(self) -> set:
        return self._page_prefetch

    @property
    def models(self) -> dict:
        models: dict = {}
        models.update(self.pages)
        models.update(self.snippets)
        models.update(self.forms)
        models.update(self.django)
        models.update((k, v[0]) for k, v in self.settings.items())
        models.update((k, v) for k, v in self.blocks.items() if not isinstance(v, tuple))
        models.update(self.scalar_blocks.items())
        return models

    @property
    def rmodels(self) -> dict:
        return dict((v, k) for k, v in self.models.items())


registry = Registry()
