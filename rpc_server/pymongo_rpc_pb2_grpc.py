# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import pymongo_rpc_pb2 as pymongo__rpc__pb2


class MongoDBServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Find = channel.unary_unary(
                '/pymongoRPC.MongoDBService/Find',
                request_serializer=pymongo__rpc__pb2.FindRequest.SerializeToString,
                response_deserializer=pymongo__rpc__pb2.FindResponse.FromString,
                )
        self.FindOne = channel.unary_unary(
                '/pymongoRPC.MongoDBService/FindOne',
                request_serializer=pymongo__rpc__pb2.FindOneRequest.SerializeToString,
                response_deserializer=pymongo__rpc__pb2.FindOneResponse.FromString,
                )
        self.InsertOne = channel.unary_unary(
                '/pymongoRPC.MongoDBService/InsertOne',
                request_serializer=pymongo__rpc__pb2.InsertOneRequest.SerializeToString,
                response_deserializer=pymongo__rpc__pb2.InsertOneResponse.FromString,
                )
        self.InsertMany = channel.unary_unary(
                '/pymongoRPC.MongoDBService/InsertMany',
                request_serializer=pymongo__rpc__pb2.InsertManyRequest.SerializeToString,
                response_deserializer=pymongo__rpc__pb2.InsertManyResponse.FromString,
                )
        self.UpdateOne = channel.unary_unary(
                '/pymongoRPC.MongoDBService/UpdateOne',
                request_serializer=pymongo__rpc__pb2.UpdateOneRequest.SerializeToString,
                response_deserializer=pymongo__rpc__pb2.UpdateOneResponse.FromString,
                )
        self.DeleteMany = channel.unary_unary(
                '/pymongoRPC.MongoDBService/DeleteMany',
                request_serializer=pymongo__rpc__pb2.DeleteManyRequest.SerializeToString,
                response_deserializer=pymongo__rpc__pb2.DeleteManyResponse.FromString,
                )
        self.CreateIndex = channel.unary_unary(
                '/pymongoRPC.MongoDBService/CreateIndex',
                request_serializer=pymongo__rpc__pb2.CreateIndexRequest.SerializeToString,
                response_deserializer=pymongo__rpc__pb2.CreateIndexResponse.FromString,
                )


class MongoDBServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Find(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FindOne(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InsertOne(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def InsertMany(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateOne(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteMany(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateIndex(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MongoDBServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Find': grpc.unary_unary_rpc_method_handler(
                    servicer.Find,
                    request_deserializer=pymongo__rpc__pb2.FindRequest.FromString,
                    response_serializer=pymongo__rpc__pb2.FindResponse.SerializeToString,
            ),
            'FindOne': grpc.unary_unary_rpc_method_handler(
                    servicer.FindOne,
                    request_deserializer=pymongo__rpc__pb2.FindOneRequest.FromString,
                    response_serializer=pymongo__rpc__pb2.FindOneResponse.SerializeToString,
            ),
            'InsertOne': grpc.unary_unary_rpc_method_handler(
                    servicer.InsertOne,
                    request_deserializer=pymongo__rpc__pb2.InsertOneRequest.FromString,
                    response_serializer=pymongo__rpc__pb2.InsertOneResponse.SerializeToString,
            ),
            'InsertMany': grpc.unary_unary_rpc_method_handler(
                    servicer.InsertMany,
                    request_deserializer=pymongo__rpc__pb2.InsertManyRequest.FromString,
                    response_serializer=pymongo__rpc__pb2.InsertManyResponse.SerializeToString,
            ),
            'UpdateOne': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateOne,
                    request_deserializer=pymongo__rpc__pb2.UpdateOneRequest.FromString,
                    response_serializer=pymongo__rpc__pb2.UpdateOneResponse.SerializeToString,
            ),
            'DeleteMany': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteMany,
                    request_deserializer=pymongo__rpc__pb2.DeleteManyRequest.FromString,
                    response_serializer=pymongo__rpc__pb2.DeleteManyResponse.SerializeToString,
            ),
            'CreateIndex': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateIndex,
                    request_deserializer=pymongo__rpc__pb2.CreateIndexRequest.FromString,
                    response_serializer=pymongo__rpc__pb2.CreateIndexResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'pymongoRPC.MongoDBService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class MongoDBService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Find(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pymongoRPC.MongoDBService/Find',
            pymongo__rpc__pb2.FindRequest.SerializeToString,
            pymongo__rpc__pb2.FindResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def FindOne(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pymongoRPC.MongoDBService/FindOne',
            pymongo__rpc__pb2.FindOneRequest.SerializeToString,
            pymongo__rpc__pb2.FindOneResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def InsertOne(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pymongoRPC.MongoDBService/InsertOne',
            pymongo__rpc__pb2.InsertOneRequest.SerializeToString,
            pymongo__rpc__pb2.InsertOneResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def InsertMany(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pymongoRPC.MongoDBService/InsertMany',
            pymongo__rpc__pb2.InsertManyRequest.SerializeToString,
            pymongo__rpc__pb2.InsertManyResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def UpdateOne(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pymongoRPC.MongoDBService/UpdateOne',
            pymongo__rpc__pb2.UpdateOneRequest.SerializeToString,
            pymongo__rpc__pb2.UpdateOneResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DeleteMany(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pymongoRPC.MongoDBService/DeleteMany',
            pymongo__rpc__pb2.DeleteManyRequest.SerializeToString,
            pymongo__rpc__pb2.DeleteManyResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CreateIndex(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/pymongoRPC.MongoDBService/CreateIndex',
            pymongo__rpc__pb2.CreateIndexRequest.SerializeToString,
            pymongo__rpc__pb2.CreateIndexResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
