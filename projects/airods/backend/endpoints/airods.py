"""
Endpoint AIRODS3 for the RAPyDo framework
EPOS-EUDAT-EOSC
"""

import os
import uuid

import dateutil.parser
from irods.query import SpecificQuery
from restapi import decorators
from restapi.exceptions import BadRequest, RestApiException
from restapi.models import PartialSchema, fields, validate
from restapi.rest.definition import EndpointResource
from restapi.utilities.logs import log

# from irods.models import Collection, DataObject
# from irods.models import User, UserGroup, UserAuth

responses = {
    200: "Successful request, results follow",
    400: "Bad request due to improper specification, unrecognised or wrong parameters",
}


#################
# INIT VARIABLES

###################
# REST CLASS Airods
#
# AIRODS - DATA
# =============
# (retrieve & download data of selected by geo-box + time-window)
#


# It is not used
# class Debug(PartialSchema):
#     debug = fields.Boolean(
#         description='Enable debugging',
#         missing=False,
#         required=False
#     )


class AirodsInput(PartialSchema):

    start = fields.DateTime(
        description="Limit to results starting on or after the specified start time in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)",
        missing=dateutil.parser.parse("2015-01-03T00:00:00Z"),
        # required=True,
    )
    end = fields.DateTime(
        description="Limit to results ending on or before the specified end time in ISO 8601 format date (yyyy-mm-ddThh:mm:ss)",
        missing=dateutil.parser.parse("2015-01-24T00:00:00Z"),
        # required=True,
    )
    minlat = fields.Float(
        description="Limit to results starting on or after the specified Latitude",
        missing=35.30,
        # required=True,
    )
    minlon = fields.Float(
        description="Limit to results starting on or after the specified Longitude",
        missing=6.30,
        # required=True,
    )
    maxlat = fields.Float(
        description="Limit to results ending on or before the specified Latitude",
        missing=46.30,
        # required=True,
    )
    maxlon = fields.Float(
        description="Limit to results ending on or before the specified Longitude",
        missing=63.30,
        # required=True,
    )

    # limit, offset and output fields are not used

    # limit = fields.Integer(
    #     description='Make query limit',
    #     missing=20,
    #     required=False
    # )
    # offset = fields.Integer(
    #     description='Make query offset',
    #     missing=0,
    #     required=False
    # )
    # output = fields.Str(
    #     description="Specifies the output format (if is set download param).",
    #     missing="json",
    #     validate=validate.OneOf(["json", "xml"]),
    #     required=False,
    # )


class Download(PartialSchema):
    download = fields.Boolean(
        description="Allow download data or retrieve PID / URI of digital object",
        required=True,
    )


class StageInput(AirodsInput):

    nscl = fields.Boolean(
        description="Select NSCL query mode (FDSN like) instead of boundingBox",
        # missing=False,
        required=True,
    )
    network = fields.Str(
        description="Select one network codes.", missing="IV", required=False
    )
    station = fields.Str(
        description="Select one station codes.",
        # missing="ACER",
        missing="*",
        required=False,
    )
    channel = fields.Str(
        description="Select one channel codes.",
        # missing="HHE",
        missing="*",
        required=False,
    )
    location = fields.Str(
        description="Select one location codes.", missing="", required=False
    )
    endpoint = fields.Str(
        description="Select target endpoint to stage data (see /list).",
        missing="TARGET",
        # required=True,
    )


class AirodsFreeInput(PartialSchema):
    remote_coll_id = fields.Str(
        description="remote collection (stage) ID to free up remote space",
        required=True,
    )


class Airods(EndpointResource):

    labels = ["airods"]

    # @decorators.auth.require()
    @decorators.use_kwargs(AirodsInput, location="query")
    @decorators.use_kwargs(Download, location="query")
    @decorators.endpoint(
        path="/airods/data",
        summary="Get data from irods-b2safe via boundingbox-timewindow (epos ecosystem)",
        responses=responses,
    )
    def get(self, start, end, minlat, minlon, maxlat, maxlon, download):
        # # --> important into mongo collections we must have:
        # #     "_cls" : "airods.models.mongo.wf_do"

        mongohd = self.get_service_instance("mongo")

        db = mongohd.variables.get("database")

        mongohd.wf_do._mongometa.connection_alias = db

        documentResult1 = []
        myLine = {}
        mycollection = mongohd.wf_do

        log.critical("start = {} ({})", start, type(start))
        log.critical("end = {} ({})", end, type(end))
        log.critical("minlat = {} ({})", minlat, type(minlat))
        log.critical("minlon = {} ({})", minlon, type(minlon))
        log.critical("maxlat = {} ({})", maxlat, type(maxlat))
        log.critical("maxlon = {} ({})", maxlon, type(maxlon))
        log.critical("download = {} ({})", download, type(download))

        try:

            myfirstvalue = mycollection.objects.raw(
                {
                    "dc_coverage_x": {"$gte": minlat, "$lte": maxlat},
                    "dc_coverage_y": {"$gte": minlon, "$lte": maxlon},
                    "dc_coverage_t_max": {"$lte": end},
                    "dc_coverage_t_min": {"$gte": start},
                }
            )

        except BaseException as e:
            raise RestApiException(e)

        for document in myfirstvalue:
            myLine["File_ID"] = document.fileId
            myLine["PID"] = document.dc_identifier
            myLine["iPath"] = document.irods_path

            documentResult1.append(myLine)

        # Download :: to check w/ irods
        if download:

            # icom = self.get_service_instance('irods')

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
                [f"total files to download: {num_files}", documentResult1]
            )


#######################
# REST CLASS AirodsMeta
#
# AIRODS - METADATA
# =================
# (retrieve metadata of selected data)
#
class AirodsMeta(EndpointResource):

    labels = ["airods"]

    @decorators.use_kwargs(AirodsInput, location="query")
    @decorators.endpoint(
        path="/airods/meta",
        summary="Get metadata from irods-b2safe via boundingbox-timewindow (epos ecosystem)",
        responses=responses,
    )
    def get(self, start, end, minlat, minlon, maxlat, maxlon):

        # # --> important! into mongo collections we must have:
        # #     "_cls" : "airods.models.mongo.wf_do"

        mongohd = self.get_service_instance("mongo")

        db = mongohd.variables.get("database")

        mongohd.wf_do._mongometa.connection_alias = db

        documentResult1 = []

        mycollection = mongohd.wf_do

        myfirstvalue = mycollection.objects.raw(
            {
                "dc_coverage_x": {"$gte": minlat, "$lte": maxlat},
                "dc_coverage_y": {"$gte": minlon, "$lte": maxlon},
                "dc_coverage_t_max": {"$lte": end},
                "dc_coverage_t_min": {"$gte": start},
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
                "irods_path": document.irods_path,
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

    labels = ["airods"]

    @decorators.endpoint(
        path="/airods/list",
        summary="Get list of endpoint to stage data (epos ecosystem)",
        responses=responses,
    )
    def get(self):

        icom = self.get_service_instance("irods")

        # where zone_type_name = 'remote'"
        sql = "select zone_name, zone_conn_string, r_comment from r_zone_main where r_comment LIKE 'stag%'"

        queryResponse = {}
        # optional, if we want to get results by key
        # columns = [DataObject.zone_id, DataObject.zone_name]
        query = SpecificQuery(icom.prc, sql)
        # register specific query in iCAT
        _ = query.register()

        for result in query:

            queryResponse["Endpoint"] = result[0]
            if result[1]:
                queryResponse["URL"] = result[1]

            if result[2]:
                queryResponse["description"] = result[2]

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

    labels = ["airods"]

    # @decorators.use_kwargs(AirodsInput)
    @decorators.use_kwargs(StageInput, location="query")
    @decorators.endpoint(
        path="/airods/stage",
        summary="Get data from irods-b2safe via boundingbox-timewindow and stage data to endpoint (epos ecosystem)",
        responses=responses,
    )
    def get(
        self, start, end, minlat, minlon, maxlat, maxlon,
    ):
        mongohd = self.get_service_instance("mongo")

        nscl = ""
        network = ""
        station = ""
        channel = ""
        location = ""
        endpoint = ""
        db = mongohd.variables.get("database")

        mongohd.wf_do._mongometa.connection_alias = db

        # MONGO

        # init
        documentResult1 = []
        myLine = {}

        mycollection = mongohd.wf_do

        log.info(nscl)

        # NSCL or BBOX
        if nscl:

            if not network:
                raise BadRequest("Missing network")

            # example of fileId "IV.ACER..HHE.D.2015.015"
            myfirstvalue = mycollection.objects.raw(
                {
                    "fileId": {
                        "$regex": f".*{network}.{station}.{channel}.{location}.*"
                    },
                    "dc_coverage_t_min": {"$gte": start},
                    "dc_coverage_t_max": {"$lte": end},
                }
            )

        else:

            myfirstvalue = mycollection.objects.raw(
                {
                    "dc_coverage_x": {"$gte": minlat, "$lte": maxlat},
                    "dc_coverage_y": {"$gte": minlon, "$lte": maxlon},
                    "dc_coverage_t_max": {"$lte": end},
                    "dc_coverage_t_min": {"$gte": start},
                }
            )

        # debug
        # for document in myfirstvalue:
        #    print  (document.irods_path)

        # return self.response(['total files staged che no: '])

        # IRODS
        icom = self.get_service_instance("irods")

        ephemeralDir = str(uuid.uuid4())
        #
        # @TODO:  multi endpoint managment

        # retrieve the stagePath from ENV AIRODS_STAGE_PATH_1
        stagePath = os.environ.get("AIRODS_STAGE_PATH_1")
        log.debug("env-path: {}", stagePath)
        if not stagePath.startswith("/"):
            stagePath = "/" + stagePath

        if not stagePath.startswith("/" + endpoint):
            raise RestApiException("Invalid stagePath or remote endpoint")

        # stagePath: '/home/rods#INGV/areastage/'
        dest_path = stagePath
        if not stagePath.endswith("/"):
            dest_path += "/"
        dest_path += ephemeralDir

        ipath = icom.create_directory(dest_path)

        if ipath is None:
            raise RestApiException(f"Failed to create {dest_path}")

        log.info("Created irods collection: {}", dest_path)

        # STAGE
        if ipath:

            # my counter
            i = 0
            for document in myfirstvalue:

                stageOk = self.icopy(
                    icom, document.irods_path, dest_path + "/" + document.fileId
                )

                if stageOk:

                    myLine["file_ID"] = str(document.fileId)
                    myLine["PID"] = str(document.dc_identifier)
                    i += 1
                    documentResult1.append(myLine)
                else:

                    myLine["DO-NOT-OK"] = "stage DO " + document.fileId + ": NOT OK"
                    documentResult1.append(myLine)

        else:

            myLine["DIR-NOT-OK"] = "stage dir:" + dest_path + " NOT OK"
            documentResult1.append(myLine)
        myLine = {}

        myLine["remote_info"] = self.queryIcat(icom, endpoint, dest_path)
        documentResult1.insert(0, myLine)

        return self.response([f"total files staged: {i}", documentResult1])

    # DO a COPY on Remote endpoint via irule
    def icopy(self, icom, irods_path, dest_path):
        """ EUDAT RULE for Replica (exploited for copy) """

        outvar = "response"
        inputs = {"*irods_path": '"%s"' % irods_path, "*stage_path": '"%s"' % dest_path}
        body = """
            *res = EUDATReplication(*irods_path, *stage_path, "false", "false", *{});
            if (*res) {{
                writeLine("stdout", "Object  replicated to stage area !");

            }}
            else {{
                writeLine("stdout", "Replication failed: *{}");
            }}
        """.format(
            outvar, outvar
        )

        rule_output = icom.rule("do_stage", body, inputs, output=True)

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
                    buf = re.sub(r'\\s+', '', buf)
                    buf = re.sub(r'\\x00', '', buf)
                    buf = buf.rstrip('\x00')
                    log.debug("Out buff: %s", buf)

                err_buf = out_array.stderrBuf.buf
                if err_buf is not None:
                    err_buf = err_buf.decode(file_coding)
                    err_buf = re.sub(r'\\s+', '', err_buf)
                    log.debug("Err buff: %s", err_buf)

                return self.response(buf)

            return self.response(raw_out)
        """

    # Exec a Query
    def queryIcat(self, icom, zone_name, dest_path):

        sql = (
            "select zone_name, zone_conn_string, r_comment   from r_zone_main where zone_name = '"
            + zone_name
            + "'"
        )
        log.debug(sql)

        # alias = 'list_zone_max'
        queryResponse = {}
        # optional, if we want to get results by key
        # columns = [DataObject.zone_id, DataObject.zone_name]
        query = SpecificQuery(icom.prc, sql)
        # register specific query in iCAT
        _ = query.register()

        queryResponse["remote_collection_ID"] = dest_path
        for result in query:

            # log.debug('Endpoint: {}', result[0])
            queryResponse["Endpoint"] = result[0]
            if result[1]:
                # log.debug('URL: {}', result[1])
                queryResponse["URL"] = result[1]
            if result[2]:
                # log.debug('description: {}', result[2])
                queryResponse["description"] = result[2]

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

    labels = ["airods"]

    @decorators.use_kwargs(AirodsFreeInput, location="query")
    @decorators.endpoint(
        path="/airods/free",
        summary="Free/delete temporary remote collection (epos ecosystem)",
        responses=responses,
    )
    def get(self, remote_coll_id):
        # documentResult = []

        log.warning("@todo: delete remote collection!")
        log.warning("@todo: empty trash remote !")
        """
        we need two rules:
        1)
        irm -r remote_coll_id

        2)
        irmtrash -rV --orphan /BINGV/trash/home/rods#INGV/trash

        """

        return self.response("ciao")
