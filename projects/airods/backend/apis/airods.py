# -*- coding: utf-8 -*-

"""
Endpoint AIRODS3 for the RAPyDo framework
EPOS-EUDAT-EOSC
"""

#################
# IMPORTS
from restapi.rest.definition import EndpointResource
from restapi.services.detect import detector
from restapi.utilities.logs import log
# from restapi.protocols.bearer import authentication
import dateutil.parser
import uuid
import subprocess

from irods.query import SpecificQuery
from irods.models import Collection, DataObject, User, UserGroup, UserAuth

from restapi.services.detect import detector
import os

#################
# INIT VARIABLES

service_name = "sqlalchemy"
# NOTE: if you need to operate based on service availability
# SERVICE_AVAILABLE = detector.check_availability(service_name)


###################
# REST CLASS Airods
#
# AIRODS - DATA
# =============
# (retrieve & download data of selected by geo-box + time-window)
#
class Airods(EndpointResource):

    labels = ['airods']
    GET = {
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
    # authentication.required()
    def get(self):
        # # --> important into mongo collections we must have:
        # #     "_cls" : "airods.models.mongo.wf_do"
        
        service = 'mongo'
        mongohd = self.get_service_instance(service_name=service)
        
        variables = detector.output_service_variables(service)
        db = variables.get('database')
        
        mongohd.wf_do._mongometa.connection_alias = db
        
        # real:
        myargs = self.get_input()
        print(myargs)
        documentResult1 = []
        myLine={}
        mycollection = mongohd.wf_do
        
        myStartDate = dateutil.parser.parse(myargs.get("start"))
        myEndDate = dateutil.parser.parse(myargs.get("end"))
        myLat = float(myargs.get("minlat"))
        myLon = float(myargs.get("minlon"))
        myLatX = float(myargs.get("maxlat"))
        myLonX = float(myargs.get("maxlon"))
        
        
        try:
        
            myfirstvalue = mycollection.objects.raw({"dc_coverage_x": { "$gte" : myLat }, "dc_coverage_y": { "$gte" : myLon }, "dc_coverage_x": { "$lte" : myLatX }, "dc_coverage_y": { "$lte" : myLonX },"dc_coverage_t_max": { "$lte" : myEndDate },"dc_coverage_t_min": { "$gte" : myStartDate } })
            
            
        except BaseException as e:
            print(e, type(e))
            return self.force_response(e)
        
        
        for document in myfirstvalue:
                myLine['File_ID'] = document.fileId
                myLine['PID'] = document.dc_identifier
                myLine['iPath'] = document.irods_path
                
                documentResult1.append(myLine)   

            
        # Download :: to check w/ irods
        if myargs.get('download') == 'true':
            
            icom = self.get_service_instance(service_name='irods') #, user='rods', password='sdor' 
            
            # @TODO: have to implement the TOTAL download not only the first - for time being-
            myobj = myfirstvalue[0].irods_path
               
            try:
                # for time being ... @TODO: allow multi files download
                #return icom.read_in_streaming(myfirstvalue[0].irods_path)
                
                for document in myfirstvalue:
                    pass
                #    print(document.irods_path)
                #    icom.read_in_streaming(document.irods_path)
                    
                # test only
                return self.force_response("TEST download Ok")
            
            except BaseException as e:
                print(e, type(e))
                return self.force_response(e)
                
            
        # Pid list :: OK
        else:
            
            return self.force_response(["total files to download: "+str(len(documentResult1)) ,documentResult1])


#######################
# REST CLASS AirodsMeta
#
# AIRODS - METADATA
# =================
# (retrieve metadata of selected data)
#
class AirodsMeta(EndpointResource):

    labels = ['airods']
    GET = {
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

    def get(self):

        # # --> important! into mongo collections we must have:
        # #     "_cls" : "airods.models.mongo.wf_do"
        
        service = 'mongo'
        mongohd = self.get_service_instance(service_name=service)
        
        variables = detector.output_service_variables(service)
        db = variables.get('database')
        
        mongohd.wf_do._mongometa.connection_alias = db
        
        # real:
        myargs = self.get_input()
        print(myargs)
        documentResult1 = []
        
        mycollection = mongohd.wf_do
        
        myStartDate = dateutil.parser.parse(myargs.get("start"))
        myEndDate = dateutil.parser.parse(myargs.get("end"))
        myLat = float(myargs.get("minlat"))
        myLon = float(myargs.get("minlon"))
        myLatX = float(myargs.get("maxlat"))
        myLonX = float(myargs.get("maxlon"))

        myfirstvalue = mycollection.objects.raw({"dc_coverage_x": { "$gte" : myLat }, "dc_coverage_y": { "$gte" : myLon }, "dc_coverage_x": { "$lte" : myLatX }, "dc_coverage_y": { "$lte" : myLonX },"dc_coverage_t_max": { "$lte" : myEndDate },"dc_coverage_t_min": { "$gte" : myStartDate } })
        #myfirstvalue = mongohd.wf_do.objects.all()
        

        for document in myfirstvalue:
             myLine = {
                "fileId" : document.fileId,
                "dc_identifier" : document.dc_identifier, 
                "dc_coverage_x" : document.dc_coverage_x, 
                "dc_coverage_y" : document.dc_coverage_y,
                "dc_coverage_z" : document.dc_coverage_z,
                "dc_title" : document.dc_title,
                "dc_subject" : document.dc_subject, 
                "dc_creator" : document.dc_creator, 
                "dc_contributor" : document.dc_contributor,
                "dc_publisher" : document.dc_publisher,
                "dc_type" : document.dc_type,
                "dc_format" : document.dc_format, 
                "dc_date" : document.dc_date, 
                "dc_coverage_t_min" : document.dc_coverage_t_min,
                "dc_coverage_t_max" : document.dc_coverage_t_max,
                "dcterms_available" : document.dcterms_available, 
                "dcterms_dateAccepted" : document.dcterms_dateAccepted, 
                "dc_rights" : document.dc_rights,
                "dcterms_isPartOf" : document.dcterms_isPartOf,
                "irods_path" : document.irods_path
             }
             documentResult1.append(myLine)

        if documentResult1 : print ("result - OK")
        #print (documentResult1)
    
        return self.force_response([documentResult1])

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
        log.debug("Connected to %s:\n%s", service_name, service_handle)

        # Handle errors
        if service_handle is None:
            log.error('Service %s unavailable', service_name)
            return self.send_errors(
                message='Server internal error. Please contact adminers.',
                # code=hcodes.HTTP_BAD_NOTFOUND
            )

        # Output any python structure (int, string, list, dictionary, etc.)
        response = 'Hello world!'
        return self.force_response(response)
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
    GET = {
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

    def get(self):
        
        icom = self.get_service_instance(service_name='irods') #, user='rods', password='sdor' 
        
        session = icom.prc
        sql = "select zone_name, zone_conn_string, r_comment   from r_zone_main where r_comment LIKE 'stag%'" #where zone_type_name = 'remote'"
        
        queryResponse = {}
        #columns = [DataObject.zone_id, DataObject.zone_name] # optional, if we want to get results by key 
        query = SpecificQuery(session, sql)
        # register specific query in iCAT
        _ = query.register()

        for result in query:
            
            queryResponse['Endpoint']=result[0]
            if result[1]:
                queryResponse['URL'] =result[1]
            
            if result[2]:
                queryResponse['description'] =result[2]
            
        _ = query.remove()
            
            
        return self.force_response([queryResponse])
    

    
    
    

        
########################
# REST CLASS AirodsStage
#
# AIRODS - STAGE
# =============
# (stage to endpoints selected data)
# 
class AirodsStage( EndpointResource):
    
    labels = ['airods']
    GET = {
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
    def get(self):
        service = 'mongo'
        mongohd = self.get_service_instance(service_name=service)
        
        variables = detector.output_service_variables(service)
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
        
        print (myargs.get("nscl"))
        
        # NSCL or BBOX
        if myargs.get("nscl") == 'true' :
            
            if myargs.get("network"):
                myNet = myargs.get("network")
            else:
                return self.force_response(['error on network declare'])
            
            if myargs.get("station"): mySta = myargs.get("station")            
            if myargs.get("channel"): myCha = myargs.get("channel")             
            if myargs.get("location"): myLoc = myargs.get("location")
            
            # example of fileId "IV.ACER..HHE.D.2015.015"            
            
            myfirstvalue = mycollection.objects.raw({"fileId": {"$regex": ".*"+myNet+"."+mySta+"."+myLoc+"."+myCha+".*"},"dc_coverage_t_min": { "$gte" : myStartDate }  , "dc_coverage_t_max": { "$lte" : myEndDate } } )       

       
        else :
           
            myLat = float(myargs.get("minlat"))
            myLon = float(myargs.get("minlon"))
            myLatX = float(myargs.get("maxlat"))
            myLonX = float(myargs.get("maxlon"))

            myfirstvalue = mycollection.objects.raw({"dc_coverage_x": { "$gte" : myLat }, "dc_coverage_y": { "$gte" : myLon }, "dc_coverage_x": { "$lte" : myLatX }, "dc_coverage_y": { "$lte" : myLonX },"dc_coverage_t_max": { "$lte" : myEndDate },"dc_coverage_t_min": { "$gte" : myStartDate } })
        
        # debug
        #for document in myfirstvalue:
        #    print  (document.irods_path)
            
        # return self.force_response(['total files staged che no: '])
        
            
        # IRODS 
        icom = self.get_service_instance(service_name='irods')
        
        ephemeralDir=str(uuid.uuid4())
        #
        # @TODO:  multi endpoint managment        
        # myvars = detector.load_group(label='airods')
        
        # retrieve the stagePath from ENV AIRODS_STAGE_PATH_1
        stagePath = os.environ.get('AIRODS_STAGE_PATH_1')
        print ("env-path: "+ stagePath )
        
        stagePath=stagePath if stagePath.startswith('/') else '/'+stagePath
        
        if stagePath.startswith('/'+myargs.get("endpoint")):
            
            # stagePath: '/home/rods#INGV/areastage/'
           
            dest_path=stagePath+ephemeralDir if stagePath.endswith('/') else stagePath+'/'+ephemeralDir
            
            
        else:
            # @TODO: to improve
            print ('ERROR - on stagePath')
            return self.force_response(['ERROR - on stagePath or remote endpoint'])
        
        ipath = icom.create_directory(dest_path)
        
        
        if ipath is None:
            raise IrodsException("Failed to create %s" % dest_path)
        else:
            log.info("Created irods collection: %s", dest_path)
        
        # STAGE
        if ipath:
            
            i = 0  #my counter
            for document in myfirstvalue:
                
                stageOk=self.icopy(icom, document.irods_path, dest_path+'/'+document.fileId)
                                
                if stageOk :
                    
                    myLine['file_ID']=str(document.fileId)
                    myLine['PID']=str(document.dc_identifier)
                    i = i+1
                    documentResult1.append(myLine)
                else:
                    
                    myLine['DO-NOT-OK']='stage DO '+document.fileId+': NOT OK'
                    documentResult1.append(myLine)
                
            
        else:
            
            myLine['DIR-NOT-OK']='stage dir:'+dest_path+' NOT OK'
            documentResult1.append(myLine)
        myLine = {}
        
        myLine['remote_info'] = self.queryIcat(icom, myargs.get("endpoint"), dest_path)            
        documentResult1.insert(0, myLine) 
        
        return self.force_response(['total files staged: '+str(i), documentResult1])
    
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
        

        rule_output = icom.rule( 'do_stage', body, inputs, output=True)
        
        return self.force_response([rule_output])
    
    
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
            msg = 'Irule failed: %s' % e.__class__.__name__
            log.error(msg)
            log.warning(e)
            # raise IrodsException(msg)
            raise e
        else:
            log.debug("Rule %s executed: %s", name, raw_out)

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

                return self.force_response(buf)

            return self.force_response(raw_out)
        """
        
    # Exec a Query
    def queryIcat(self, icom, zone_name, dest_path):
        
        session = icom.prc
        sql = "select zone_name, zone_conn_string, r_comment   from r_zone_main where zone_name = '"+zone_name+"'" 
        print (sql)
        
        #alias = 'list_zone_max'
        queryResponse = {}
        #columns = [DataObject.zone_id, DataObject.zone_name] # optional, if we want to get results by key 
        query = SpecificQuery(session, sql)
        # register specific query in iCAT
        _ = query.register()
        
        queryResponse['remote_collection_ID']=dest_path
        for result in query:
            
            #print('Endpoint: '+result[0])
            queryResponse['Endpoint']=result[0]
            if result[1]:
                #print('URL: '+result[1])
                queryResponse['URL'] =result[1]
            #else:
                #print('URL: ')
            if result[2]:
                #print('description: '+result[2])
                queryResponse['description'] =result[2]
            #else:
                #print('description: ')
            

            #print('{} {}'.format(result[zone_id], result[zone_name]))


        _ = query.remove()
        
        return self.force_response(queryResponse)
        

#################
# REST CLASS AirodsFree
#
# AIRODS - FREE
# =============
# (free up space on the remote endpoints)  --> probably will  not be used 
#        
class AirodsFree( EndpointResource):
    
    labels = ['airods']
    GET = {
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

    def get(self):
        myargs = self.get_input()
        print(myargs)
        documentResult = []
        
        collection_to_del = myargs.get("remote_coll_id")
        print ('@todo: delete remote collection!')
        print ('@todo: empty trash remote !')
        """
        we need two rules:
        1)
        irm -r collection_to_del
        
        2)
        irmtrash -rV --orphan /BINGV/trash/home/rods#INGV/trash
        
        """
        
        
        return self.force_response(['ciao'])
