add_subdirectory(whale)
simcenter_add_python_script(SCRIPT femUQ.py)
simcenter_add_python_script(SCRIPT changeJSON.py)
simcenter_add_python_script(SCRIPT "sWHALE.py")
simcenter_add_python_script(SCRIPT "qWHALE.py")
simcenter_add_python_script(SCRIPT "rWHALE.py")
simcenter_add_python_script(SCRIPT "createResponseCSV.py")
simcenter_add_python_script(SCRIPT "siteResponseWHALE.py")
simcenter_add_python_script(SCRIPT "createGM4BIM.py")
simcenter_add_python_script(SCRIPT "computeResponseSpectrum.py")
simcenter_add_python_script(SCRIPT RegionalEarthquakeSimulation.py)
simcenter_add_python_script(SCRIPT WorkflowUtils.py)
simcenter_add_python_script(SCRIPT MultiModelApplication.py)
simcenter_add_python_script(SCRIPT MultiModelDriver.py)

simcenter_add_file(NAME WorkflowApplications.json)

simcenter_add_python_script(SCRIPT SiteResponse_workflow.py)
simcenter_add_python_script(SCRIPT R2DTool_workflow.py)
simcenter_add_python_script(SCRIPT CreateWorkflowJobs.py)

simcenter_add_executable(NAME runMultiModelDriver
                         FILES runMultiModelDriver.cpp)
