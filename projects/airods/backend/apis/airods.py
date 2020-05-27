# -*- coding: utf-8 -*-

"""
Endpoint AIRODS3 for the RAPyDo framework
EPOS-EUDAT-EOSC
"""

import os
import uuid
import dateutil.parser
from irods.query import SpecificQuery
# from irods.models import Collection, DataObject
# from irods.models import User, UserGroup, UserAuth

from restapi.rest.definition import EndpointResource
from restapi.services.detect import Detector
from restapi.utilities.logs import log
from restapi import decorators
from restapi.exceptions import RestApiException

#################
# INIT VARIABLES

###################
# REST CLASS Airods
#
# AIRODS - DATA
# =============
# (retrieve & download data of selected by geo-box + time-window)
#
class Airods(EndpointResource):

    labels = ['airods']
    _GET = {
        '/airods/data': {
            'summary': 'Get data from iRODS-B2SAFE via boundingBox-timeWindow  (Epos ecosystem)',
            'parameters': [
                {'name': 'debug', 'description': 'for debugging', 'in': 'query', 'type': 'string', 'default': 'no', 'required': False},
                {'name': 'start', 'description': 'Limit to results starting on or after the specified start time in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)', 'in': 'query', 'type': 'string', 'default': '2015-01-03T00:00:00Z', 'required': True},
                {'name': 'end', 'description': 'Limit to results ending on or before the specified end time in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)', 'in': 'query', 'type': 'string', 'default': '2015-01-24T00:00:00Z', 'required': True},
                {'name': 'minlat', 'description': 'Limit to results starting on or after the specified Latitude', 'in': 'query', 'type': 'string', 'default': '35.30', 'required': True},
                {'name': 'minlon', 'description': 'Limit to results starting on or after the specified start Longitude', 'in': 'query', 'type': 'string', 'default': '6.30', 'required': True},
                {'name': 'maxlat', 'description': 'Limit to results ending on or before the specified end Latitude', 'in': 'query', 'type': 'string', 'default': '46.30', 'required': True},
                {'name': 'maxlon', 'description': 'Limit to results ending on or before the specified end Longitude', 'in': 'query', 'type': 'string', 'default': '63.30', 'required': True},
                {'name': 'download', 'description': 'Allow download data  or retrieve PID / URI of digital object', 'in': 'query', 'type': 'boolean', 'default': False, 'required': True},
                {'name': 'limit', 'description': 'Make query limit (default=20)', 'in': 'query', 'type': 'string', 'default': '0', 'required': False},
                {'name': 'offset', 'description': 'Make query offset (default=0)', 'in': 'query', 'type': 'string', 'default': '20', 'required': False},
                {'name': 'output', 'description': 'Specifies the desired output format (if is set download param). Valid json values xml, json', 'in': 'query', 'type': 'string', 'default': 'json', 'required': False}
            ],
            'responses': {
                '200': {'description': 'Successful request, results follow'},
                '204': {'description': 'Request was properly formatted and submitted but no data matches the selection'},
                '400': {'description': 'Bad request due to improper specification, unrecognised parameter, parameter value out of range, etc.'},
                '413': {'description': 'Request would result in too much data being returned or the request itself is too large.'},
                '500': {'description': 'Internal server error'},
                '503': {'description': 'Service temporarily unavailable, used in maintenance mode'}
            }
        }
    }

    # @decorators.auth.required()
    @decorators.catch_errors()
    def get(self):
        # # --> important into mongo collections we must have:
        # #     "_cls" : "airods.models.mongo.wf_do"

        mongohd = self.get_service_instance(service_name='mongo')

        variables = Detector.load_variables(prefix='mongo')
        db = variables.get('database')

        mongohd.wf_do._mongometa.connection_alias = db

        # real:
        myargs = self.get_input()
        log.debug(myargs)
        documentResult1 = []
        myLine = {}
        mycollection = mongohd.wf_do

        myStartDate = dateutil.parser.parse(myargs.get("start"))
        myEndDate = dateutil.parser.parse(myargs.get("end"))
        myLat = float(myargs.get("minlat"))
        myLon = float(myargs.get("minlon"))
        myLatX = float(myargs.get("maxlat"))
        myLonX = float(myargs.get("maxlon"))

        try:

            myfirstvalue = mycollection.objects.raw(
                {
                    "dc_coverage_x": {"$gte": myLat},
                    "dc_coverage_y": {"$gte": myLon},
                    "dc_coverage_x": {"$lte": myLatX},
                    "dc_coverage_y": {"$lte": myLonX},
                    "dc_coverage_t_max": {"$lte": myEndDate},
                    "dc_coverage_t_min": {"$gte": myStartDate}
                }
            )

        except BaseException as e:
            raise RestApiException(e)

        for document in myfirstvalue:
            myLine['File_ID'] = document.fileId
            myLine['PID'] = document.dc_identifier
            myLine['iPath'] = document.irods_path

            documentResult1.append(myLine)

        # Download :: to check w/ irods
        if myargs.get('download') == 'true':

            # icom = self.get_service_instance(service_name='irods')

            # @TODO: have to implement the TOTAL download not only the first
            # myobj = myfirstvalue[0].irods_path

            try:
                # for time being ... @TODO: allow multi files download
                # return icom.read_in_streaming(myfirstvalue[0].irods_path)

                for document in myfirstvalue:
                    pass
                #    log.debug(document.irods_path)
                #    icom.read_in_streaming(document.irods_path)

                # test only
                return self.response("TEST download Ok")

            except BaseException as e:
                raise RestApiException(e)

        # Pid list :: OK
        else:

            num_files = len(documentResult1)
            return self.response(
                [
                    "total files to download: {}".format(num_files),
                    documentResult1
                ]
            )


#######################
# REST CLASS AirodsMeta
#
# AIRODS - METADATA
# =================
# (retrieve metadata of selected data)
#
class AirodsMeta(EndpointResource):

    labels = ['airods']
    _GET = {
        '/airods/meta': {
            'summary': 'Get Metadata from iRODS-B2SAFE via boundingBox-timeWindow (Epos ecosystem)',
            'parameters': [
                {'name': 'debug', 'description': 'for debugging', 'in': 'query', 'type': 'string', 'default': 'no', 'required': False},
                {'name': 'start', 'description': 'Limit to results starting on or after the specified start  in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)', 'in': 'query', 'type': 'string', 'default': '2015-01-13T00:00:00Z', 'required': True},
                {'name': 'end', 'description': 'Limit to results ending on or before the specified end time in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)', 'in': 'query', 'type': 'string', 'default': '2015-01-14T00:00:00Z', 'required': True},
                {'name': 'minlat', 'description': 'Limit to results starting on or after the specified Latitude', 'in': 'query', 'type': 'string', 'default': '35.30', 'required': True},
                {'name': 'minlon', 'description': 'Limit to results starting on or after the specified start Longitude', 'in': 'query', 'type': 'string', 'default': '6.30', 'required': True},
                {'name': 'maxlat', 'description': 'Limit to results ending on or before the specified end Latitude', 'in': 'query', 'type': 'string', 'default': '46.30', 'required': True},
                {'name': 'maxlon', 'description': 'Limit to results ending on or before the specified end Longitude', 'in': 'query', 'type': 'string', 'default': '63.30', 'required': True},
                {'name': 'limit', 'description': 'Make query limit (default=20)', 'in': 'query', 'type': 'string', 'default': '0', 'required': False},
                {'name': 'offset', 'description': 'Make query offset (default=0)', 'in': 'query', 'type': 'string', 'default': '20', 'required': False},
                {'name': 'output', 'description': 'Specifies the desired output format (if is set download param). Valid json values xml, json', 'in': 'query', 'type': 'string', 'default': 'json', 'required': False}
            ],
            'responses': {
                '200': {'description': 'Successful request, results follow'},
                '204': {'description': 'Request was properly formatted and submitted but no data matches the selection'},
                '400': {'description': 'Bad request due to improper specification, unrecognised parameter, parameter value out of range, etc.'},
                '413': {'description': 'Request would result in too much data being returned or the request itself is too large.'},
                '500': {'description': 'Internal server error'},
                '503': {'description': 'Service temporarily unavailable, used in maintenance mode'}
            }
        }
    }

    @decorators.catch_errors()
    def get(self):

        # # --> important! into mongo collections we must have:
        # #     "_cls" : "airods.models.mongo.wf_do"

        mongohd = self.get_service_instance(service_name='mongo')

        variables = Detector.load_variables(prefix='mongo')
        db = variables.get('database')

        mongohd.wf_do._mongometa.connection_alias = db

        # real:
        myargs = self.get_input()
        log.debug(myargs)
        documentResult1 = []

        mycollection = mongohd.wf_do

        myStartDate = dateutil.parser.parse(myargs.get("start"))
        myEndDate = dateutil.parser.parse(myargs.get("end"))
        myLat = float(myargs.get("minlat"))
        myLon = float(myargs.get("minlon"))
        myLatX = float(myargs.get("maxlat"))
        myLonX = float(myargs.get("maxlon"))

        myfirstvalue = mycollection.objects.raw(
            {
                "dc_coverage_x": {"$gte": myLat},
                "dc_coverage_y": {"$gte": myLon},
                "dc_coverage_x": {"$lte": myLatX},
                "dc_coverage_y": {"$lte": myLonX},
                "dc_coverage_t_max": {"$lte": myEndDate},
                "dc_coverage_t_min": {"$gte": myStartDate}
            }
        )
        # myfirstvalue = mongohd.wf_do.objects.all()

        for document in myfirstvalue:
            myLine = {
                "fileId": document.fileId,
                "dc_identifier": document.dc_identifier,
                "dc_coverage_x": document.dc_coverage_x,
                "dc_coverage_y": document.dc_coverage_y,
                "dc_coverage_z": document.dc_coverage_z,
                "dc_title": document.dc_title,
                "dc_subject": document.dc_subject,
                "dc_creator": document.dc_creator,
                "dc_contributor": document.dc_contributor,
                "dc_publisher": document.dc_publisher,
                "dc_type": document.dc_type,
                "dc_format": document.dc_format,
                "dc_date": document.dc_date,
                "dc_coverage_t_min": document.dc_coverage_t_min,
                "dc_coverage_t_max": document.dc_coverage_t_max,
                "dcterms_available": document.dcterms_available,
                "dcterms_dateAccepted": document.dcterms_dateAccepted,
                "dc_rights": document.dc_rights,
                "dcterms_isPartOf": document.dcterms_isPartOf,
                "irods_path": document.irods_path
            }
            documentResult1.append(myLine)

        if documentResult1:
            log.info("result - OK")
        # log.info (documentResult1)

        return self.response([documentResult1])

        """
        # Write server logs, on different levels:
        # very_verbose, verbose, debug, info, warning, error, critical, exit
        log.info("Received a test HTTP request")

        # Parse input parameters:
        # NOTE: they can be caught only if indicated in swagger files
        self.get_input()
        # pretty print arguments obtained from the _args private attribute
        log.pp(self._args, prefix_line='Parsed args')

        # Activate a service handle
        service_handle = self.get_service_instance(service_name)
        log.debug("Connected to {}:\n{}", service_name, service_handle)

        # Handle errors
        if service_handle is None:
            log.error('Service {} unavailable', service_name)
            raise RestApiException('Server internal error. Please contact adminers.')

        # Output any python structure (int, string, list, dictionary, etc.)
        response = 'Hello world!'
        return self.response(response)
        """


#######################
# REST CLASS AirodsList
#
# AIRODS - LIST
# =============
# (list of endpoints to stage data)
#
class AirodsList(EndpointResource):

    labels = ['airods']
    _GET = {
        '/airods/list': {
            'summary': 'Get List of endpoint to stage data  (Epos ecosystem)',
            'parameters': [
                {'name': 'debug', 'description': 'for debugging', 'in': 'query', 'type': 'string', 'default': 'no', 'required': False}
            ],
            'responses': {
                '200': {'description': 'Successful request, results follow'},
                '204': {'description': 'Request was properly formatted and submitted but no data matches the selection'},
                '400': {'description': 'Bad request due to improper specification, unrecognised parameter, parameter value out of range, etc.'},
                '413': {'description': 'Request would result in too much data being returned or the request itself is too large.'},
                '500': {'description': 'Internal server error'},
                '503': {'description': 'Service temporarily unavailable, used in maintenance mode'}
            }
        }
    }

    @decorators.catch_errors()
    def get(self):

        icom = self.get_service_instance(service_name='irods')

        session = icom.prc
        # where zone_type_name = 'remote'"
        sql = "select zone_name, zone_conn_string, r_comment from r_zone_main where r_comment LIKE 'stag%'"

        queryResponse = {}
        # optional, if we want to get results by key
        # columns = [DataObject.zone_id, DataObject.zone_name]
        query = SpecificQuery(session, sql)
        # register specific query in iCAT
        _ = query.register()

        for result in query:

            queryResponse['Endpoint'] = result[0]
            if result[1]:
                queryResponse['URL'] = result[1]

            if result[2]:
                queryResponse['description'] = result[2]

        query.remove()

        return self.response([queryResponse])


########################
# REST CLASS AirodsStage
#
# AIRODS - STAGE
# =============
# (stage to endpoints selected data)
#
class AirodsStage(EndpointResource):

    labels = ['airods']
    _GET = {
        '/airods/stage': {
            'summary': 'Get data from iRODS-B2SAFE via boundingBox-timeWindow and stage data to endpoint (Epos ecosystem)',
            'parameters': [
                {'name': 'debug', 'description': 'for debugging', 'in': 'query', 'type': 'string', 'default': 'no', 'required': False},
                {'name': 'start', 'description': 'Limit to results starting on or after the specified start  in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)', 'in': 'query', 'type': 'string', 'default': '2015-01-13T00:00:00Z', 'required': True},
                {'name': 'end', 'description': 'Limit to results ending on or before the specified end time in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)', 'in': 'query', 'type': 'string', 'default': '2015-01-14T00:00:00Z', 'required': True},
                {'name': 'minlat', 'description': 'Limit to results starting on or after the specified Latitude', 'in': 'query', 'type': 'string', 'default': '35.30', 'required': False},
                {'name': 'minlon', 'description': 'Limit to results starting on or after the specified start Longitude', 'in': 'query', 'type': 'string', 'default': '6.30', 'required': False},
                {'name': 'maxlat', 'description': 'Limit to results ending on or before the specified end Latitude', 'in': 'query', 'type': 'string', 'default': '46.30', 'required': False},
                {'name': 'maxlon', 'description': 'Limit to results ending on or before the specified end Longitude', 'in': 'query', 'type': 'string', 'default': '13.30', 'required': False},
                {'name': 'nscl', 'description': 'Select NSCL query mode (FDSN like) instead of boundingBox (default)', 'in': 'query', 'type': 'boolean', 'default': 'false', 'required': True},
                {'name': 'network', 'description': 'Select one network codes.', 'in': 'query', 'type': 'string', 'default': 'IV', 'required': False},
                {'name': 'station', 'description': 'Select one station codes.', 'in': 'query', 'type': 'string', 'default': 'ACER', 'required': False},
                {'name': 'channel', 'description': 'Select one channel codes.', 'in': 'query', 'type': 'string', 'default': 'HHE', 'required': False},
                {'name': 'location', 'description': 'Select one location codes.', 'in': 'query', 'type': 'string', 'default': '', 'required': False},
                {'name': 'endpoint', 'description': 'Select target endpoint to stage data (see /list).', 'in': 'query', 'type': 'string', 'default': 'TARGET', 'required': True},
                {'name': 'limit', 'description': 'Make query limit (default=20)', 'in': 'query', 'type': 'string', 'default': '0', 'required': False},
                {'name': 'offset', 'description': 'Make query offset (default=0)', 'in': 'query', 'type': 'string', 'default': '20', 'required': False}
            ],
            'responses': {
                '200': {'description': 'Successful request, results follow'},
                '204': {'description': 'Request was properly formatted and submitted but no data matches the selection'},
                '400': {'description': 'Bad request due to improper specification, unrecognised parameter, parameter value out of range, etc.'},
                '413': {'description': 'Request would result in too much data being returned or the request itself is too large.'},
                '500': {'description': 'Internal server error'},
                '503': {'description': 'Service temporarily unavailable, used in maintenance mode'}
            }
        }
    }

    @decorators.catch_errors()
    def get(self):
        mongohd = self.get_service_instance(service_name='mongo')

        variables = Detector.load_variables(prefix='mongo')
        db = variables.get('database')

        mongohd.wf_do._mongometa.connection_alias = db

        # MONGO
        myargs = self.get_input()
        # debug
        print(myargs)

        # init
        documentResult1 = []
        myLine = {}

        myLat = ""
        myLon = ""
        myLatX = ""
        myLonX = ""

        myNet = ""
        mySta = "*"
        myCha = "*"
        myLoc = ""

        mycollection = mongohd.wf_do

        # get params
        myStartDate = dateutil.parser.parse(myargs.get("start"))
        myEndDate = dateutil.parser.parse(myargs.get("end"))

        log.info(myargs.get("nscl"))

        # NSCL or BBOX
        if myargs.get("nscl") == 'true':

            if myargs.get("network"):
                myNet = myargs.get("network")
            else:
                return self.response(['error on network declare'])

            if myargs.get("station"):
                mySta = myargs.get("station")
            if myargs.get("channel"):
                myCha = myargs.get("channel")
            if myargs.get("location"):
                myLoc = myargs.get("location")

            # example of fileId "IV.ACER..HHE.D.2015.015"

            myfirstvalue = mycollection.objects.raw(
                {
                    "fileId": {
                        "$regex": ".*" + myNet + "." + mySta + "." + myLoc + "." + myCha + ".*"
                    },
                    "dc_coverage_t_min": {"$gte": myStartDate},
                    "dc_coverage_t_max": {"$lte": myEndDate}
                }
            )

        else:

            myLat = float(myargs.get("minlat"))
            myLon = float(myargs.get("minlon"))
            myLatX = float(myargs.get("maxlat"))
            myLonX = float(myargs.get("maxlon"))

            myfirstvalue = mycollection.objects.raw(
                {
                    "dc_coverage_x": {"$gte": myLat},
                    "dc_coverage_y": {"$gte": myLon},
                    "dc_coverage_x": {"$lte": myLatX},
                    "dc_coverage_y": {"$lte": myLonX},
                    "dc_coverage_t_max": {"$lte": myEndDate},
                    "dc_coverage_t_min": {"$gte": myStartDate}
                }
            )

        # debug
        # for document in myfirstvalue:
        #    print  (document.irods_path)

        # return self.response(['total files staged che no: '])

        # IRODS
        icom = self.get_service_instance(service_name='irods')

        ephemeralDir = str(uuid.uuid4())
        #
        # @TODO:  multi endpoint managment
        # myvars = detector.load_group(label='airods')

        # retrieve the stagePath from ENV AIRODS_STAGE_PATH_1
        stagePath = os.environ.get('AIRODS_STAGE_PATH_1')
        log.debug("env-path: {}", stagePath)
        if not stagePath.startswith('/'):
            stagePath = '/' + stagePath

        if stagePath.startswith('/' + myargs.get("endpoint")):

            # stagePath: '/home/rods#INGV/areastage/'
            dest_path = stagePath
            if not stagePath.endswith('/'):
                dest_path += '/'
            dest_path += ephemeralDir

        else:
            raise RestApiException("Invalid stagePath or remote endpoint")

        ipath = icom.create_directory(dest_path)

        if ipath is None:
            raise RestApiException("Failed to create {}".format(dest_path))

        log.info("Created irods collection: {}", dest_path)

        # STAGE
        if ipath:

            # my counter
            i = 0
            for document in myfirstvalue:

                stageOk = self.icopy(
                    icom,
                    document.irods_path,
                    dest_path + '/' + document.fileId
                )

                if stageOk:

                    myLine['file_ID'] = str(document.fileId)
                    myLine['PID'] = str(document.dc_identifier)
                    i += 1
                    documentResult1.append(myLine)
                else:

                    myLine['DO-NOT-OK'] = 'stage DO ' + document.fileId + ': NOT OK'
                    documentResult1.append(myLine)

        else:

            myLine['DIR-NOT-OK'] = 'stage dir:' + dest_path + ' NOT OK'
            documentResult1.append(myLine)
        myLine = {}

        myLine['remote_info'] = self.queryIcat(icom, myargs.get("endpoint"), dest_path)
        documentResult1.insert(0, myLine)

        return self.response(
            [
                'total files staged: {}'.format(i),
                documentResult1
            ]
        )

    # DO a COPY on Remote endpoint via irule
    def icopy(self, icom, irods_path, dest_path):
        """ EUDAT RULE for Replica (exploited for copy) """

        outvar = 'response'
        inputs = {
            '*irods_path': '"%s"' % irods_path,
            '*stage_path': '"%s"' % dest_path
        }
        body = """
            *res = EUDATReplication(*irods_path, *stage_path, "false", "false", *%s);
            if (*res) {
                writeLine("stdout", "Object  replicated to stage area !");

            }
            else {
                writeLine("stdout", "Replication failed: *%s");
            }
        """ % (outvar, outvar)

        rule_output = icom.rule('do_stage', body, inputs, output=True)

        return [rule_output]

    # Exec a Rule
    """
    def rule(self, icom, name, body, inputs, output=False):

        import textwrap
        from irods.rule import Rule

        user_current = icom.prc.username
        zone_current = icom.prc.zone

        #rule_body = textwrap.dedent(''' #\
        #    %s {{
        #        %s
        #}}''' % (name, body))
        '''
        outname = None
        if output:
            outname = 'ruleExecOut'

        myrule = Rule(icom.prc, body=rule_body, params=inputs, output=outname)
        try:
            raw_out = myrule.execute()
        except BaseException as e:
            msg = 'Irule failed: {}'.format(e.__class__.__name__)
            # raise RestApiException(msg)
        else:
            log.debug("Rule {} executed: {}", name, raw_out)

            # retrieve out buffer
            if output and len(raw_out.MsParam_PI) > 0:
                out_array = raw_out.MsParam_PI[0].inOutStruct
                # print("out array", out_array)

                import re
                file_coding = 'utf-8'

                buf = out_array.stdoutBuf.buf
                if buf is not None:
                    # it's binary data (BinBytesBuf) so must be decoded
                    buf = buf.decode(file_coding)
                    buf = re.sub(r'\s+', '', buf)
                    buf = re.sub(r'\\x00', '', buf)
                    buf = buf.rstrip('\x00')
                    log.debug("Out buff: %s", buf)

                err_buf = out_array.stderrBuf.buf
                if err_buf is not None:
                    err_buf = err_buf.decode(file_coding)
                    err_buf = re.sub(r'\s+', '', err_buf)
                    log.debug("Err buff: %s", err_buf)

                return self.response(buf)

            return self.response(raw_out)
        """

    # Exec a Query
    def queryIcat(self, icom, zone_name, dest_path):

        session = icom.prc
        sql = "select zone_name, zone_conn_string, r_comment   from r_zone_main where zone_name = '" + zone_name + "'"
        log.debug(sql)

        # alias = 'list_zone_max'
        queryResponse = {}
        # optional, if we want to get results by key
        # columns = [DataObject.zone_id, DataObject.zone_name]
        query = SpecificQuery(session, sql)
        # register specific query in iCAT
        _ = query.register()

        queryResponse['remote_collection_ID'] = dest_path
        for result in query:

            # log.debug('Endpoint: {}', result[0])
            queryResponse['Endpoint'] = result[0]
            if result[1]:
                # log.debug('URL: {}', result[1])
                queryResponse['URL'] = result[1]
            if result[2]:
                # log.debug('description: {}', result[2])
                queryResponse['description'] = result[2]

            # log.info('{} {}', result[zone_id], result[zone_name])

        query.remove()

        return self.response(queryResponse)


#################
# REST CLASS AirodsFree
#
# AIRODS - FREE
# =============
# (free up space on the remote endpoints)  --> probably will  not be used
#
class AirodsFree(EndpointResource):

    labels = ['airods']
    _GET = {
        '/airods/free': {
            'summary': 'free/delete temporary remote collection  (Epos ecosystem)',
            'parameters': [
                {'name': 'debug', 'description': 'for debugging', 'in': 'query', 'type': 'string', 'default': 'no', 'required': False},
                {'name': 'remote_coll_id', 'description': 'remote collection (stage) ID to free up remote space', 'in': 'query', 'type': 'string', 'default': 'none', 'required': True}
            ],
            'responses': {
                '200': {'description': 'Successful request, results follow'},
                '204': {'description': 'Request was properly formatted and submitted but no data matches the selection'},
                '400': {'description': 'Bad request due to improper specification, unrecognised parameter, parameter value out of range, etc.'},
                '413': {'description': 'Request would result in too much data being returned or the request itself is too large.'},
                '500': {'description': 'Internal server error'},
                '503': {'description': 'Service temporarily unavailable, used in maintenance mode'}
            }
        }
    }

    @decorators.catch_errors()
    def get(self):
        myargs = self.get_input()
        log.debug(myargs)
        # documentResult = []

        # collection_to_del = myargs.get("remote_coll_id")
        log.warning('@todo: delete remote collection!')
        log.warning('@todo: empty trash remote !')
        """
        we need two rules:
        1)
        irm -r collection_to_del

        2)
        irmtrash -rV --orphan /BINGV/trash/home/rods#INGV/trash

        """

        return self.response(['ciao'])
