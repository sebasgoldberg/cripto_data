import graphene

from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from fetch_data.models import Price

class PriceNode(DjangoObjectType):
    class Meta:
        model = Price
        filter_fields = {
            'currency': ['exact', ],
        }
        interfaces = (graphene.relay.Node, )

class Query(object):
    price = graphene.relay.Node.Field(PriceNode)
    all_prices = DjangoFilterConnectionField(PriceNode)
