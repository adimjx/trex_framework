# server/gql/router.py

import strawberry
from strawberry.fastapi import GraphQLRouter
from .client_info.queries import ClientInfo

@strawberry.type
class Queries(ClientInfo):
    pass

# @strawberry.type
# class Mutations():
#     pass

schema = strawberry.Schema(query=Queries)#, mutation=Mutations)
graphql_app = GraphQLRouter(schema)