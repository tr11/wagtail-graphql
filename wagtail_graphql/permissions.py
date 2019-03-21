# python
from typing import Any, Union
# django
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser
# wagtail
from wagtail.core.query import PageQuerySet
from wagtail.core.models import PageViewRestriction, CollectionViewRestriction
from wagtail.images.models import ImageQuerySet
from wagtail.documents.models import DocumentQuerySet


def with_page_permissions(request: Any, queryset: PageQuerySet) -> PageQuerySet:
    user = request.user

    # Filter by site
    if request.site:
        queryset = queryset.descendant_of(request.site.root_page, inclusive=True)
    else:
        # No sites configured
        return queryset.none()  # pragma: no cover

    # Get live pages that are public and check groups and login permissions
    if user == AnonymousUser:
        queryset = queryset.public()
    elif user.is_superuser:
        pass
    else:
        current_user_groups = user.groups.all()
        q = Q()
        for restriction in PageViewRestriction.objects.all():
            if (restriction.restriction_type == PageViewRestriction.PASSWORD) or \
                    (restriction.restriction_type == PageViewRestriction.LOGIN and not user.is_authenticated) or \
                    (restriction.restriction_type == PageViewRestriction.GROUPS and
                     not any(group in current_user_groups for group in restriction.groups.all())
                     ):
                q = ~queryset.descendant_of_q(restriction.page, inclusive=True)
        queryset = queryset.filter(q).live()

    return queryset


CollectionQSType = Union[ImageQuerySet, DocumentQuerySet]


def with_collection_permissions(request: Any, queryset: CollectionQSType) -> CollectionQSType:
    user = request.user

    # Get live pages that are public and check groups and login permissions
    if user == AnonymousUser:
        queryset = queryset.public()
    elif user.is_superuser:
        pass
    else:
        current_user_groups = user.groups.all()
        q = Q()
        for restriction in CollectionViewRestriction.objects.all():
            if (restriction.restriction_type == CollectionViewRestriction.PASSWORD) or \
                    (restriction.restriction_type == CollectionViewRestriction.LOGIN and not user.is_authenticated) or \
                    (restriction.restriction_type == CollectionViewRestriction.GROUPS and
                     not any(group in current_user_groups for group in restriction.groups.all())
                     ):
                q &= ~Q(collection=restriction.collection)
                # q &= ~queryset.filter(collection) descendant_of_q(restriction.page, inclusive=True)
        queryset = queryset.filter(q)

    return queryset
