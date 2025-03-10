# Site response workflow  # noqa: INP001, D100

import argparse
import json
import os
import sys
from glob import glob
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))  # noqa: PTH120

import whale.main as whale
from whale.main import log_div, log_msg


def main(  # noqa: D103
    run_type,
    input_file,
    app_registry,
    force_cleanup,
    bldg_id_filter,
    reference_dir,
    working_dir,
    app_dir,
    log_file,
):
    # initialize the log file
    with open(input_file) as f:  # noqa: PTH123
        inputs = json.load(f)
    if working_dir is not None:
        runDir = working_dir  # noqa: N806
    else:
        runDir = inputs['runDir']  # noqa: N806

    if not os.path.exists(runDir):  # noqa: PTH110
        os.mkdir(runDir)  # noqa: PTH102
    if log_file == 'log.txt':
        whale.log_file = runDir + '/log.txt'
    else:
        whale.log_file = log_file
    with open(whale.log_file, 'w') as f:  # noqa: PTH123
        f.write('RDT workflow\n')

    whale.print_system_info()

    # echo the inputs
    log_msg(log_div)
    log_msg('Started running the workflow script')
    log_msg(log_div)
    if force_cleanup:
        log_msg('Forced cleanup turned on.')

    WF = whale.Workflow(  # noqa: N806
        run_type,
        input_file,
        app_registry,
        app_type_list=[
            'Building',
            'RegionalEvent',
            'RegionalMapping',
            'Event',
            'Modeling',
            'EDP',
            'Simulation',
            'UQ',
            'DL',
        ],
        reference_dir=reference_dir,
        working_dir=working_dir,
        app_dir=app_dir,
        units=inputs.get('units', None),
        outputs=inputs.get('outputs', None),
    )

    if bldg_id_filter is not None:
        print(bldg_id_filter)  # noqa: T201
        log_msg(f'Overriding simulation scope; running buildings {bldg_id_filter}')

        # If a Min or Max attribute is used when calling the script, we need to
        # update the min and max values in the input file.
        WF.workflow_apps['Building'].pref['filter'] = bldg_id_filter

    # initialize the working directory
    WF.init_workdir()

    # prepare the basic inputs for individual buildings
    building_file = WF.create_building_files()
    WF.perform_regional_mapping(building_file)

    # TODO: not elegant code, fix later  # noqa: TD002
    with open(WF.building_file_path) as f:  # noqa: PTH123
        bldg_data = json.load(f)

    for bldg in bldg_data:  # [:1]:
        log_msg(bldg)

        # initialize the simulation directory
        WF.init_simdir(bldg['id'], bldg['file'])

        # prepare the input files for the simulation
        WF.create_RV_files(
            app_sequence=['Event', 'Modeling', 'EDP', 'Simulation'],
            BIM_file=bldg['file'],
            bldg_id=bldg['id'],
        )

        # create the workflow driver file
        WF.create_driver_file(
            app_sequence=['Building', 'Event', 'Modeling', 'EDP', 'Simulation'],
            bldg_id=bldg['id'],
        )

        # run uq engine to simulate response
        WF.simulate_response(BIM_file=bldg['file'], bldg_id=bldg['id'])

        # run dl engine to estimate losses
        # WF.estimate_losses(BIM_file = bldg['file'], bldg_id = bldg['id'])

        if force_cleanup:
            # clean up intermediate files from the simulation
            WF.cleanup_simdir(bldg['id'])

    # aggregate results
    # WF.aggregate_results(bldg_data = bldg_data)

    if force_cleanup:
        # clean up intermediate files from the working directory
        WF.cleanup_workdir()

    surfaceMoDir = collect_surface_motion(WF.run_dir, bldg_data)  # noqa: N806, F841


def collect_surface_motion(runDir, bldg_data, surfaceMoDir=''):  # noqa: N803, D103
    if surfaceMoDir == '':
        surfaceMoDir = f'{runDir}/surface_motions/'  # noqa: N806

    for bldg in bldg_data:  # [:1]:
        log_msg(bldg)

        bldg_id = bldg['id']

        if bldg_id is not None:
            mPaths = glob(f'{runDir}/{bldg_id}/workdir.*/EVENT.json')  # noqa: PTH207, N806

            surfMoTmpDir = f'{surfaceMoDir}/{bldg_id}/'  # noqa: N806

            if not os.path.exists(surfMoTmpDir):  # noqa: PTH110
                os.makedirs(surfMoTmpDir)  # noqa: PTH103

            for p in mPaths:
                simID = p.split('/')[-2].split('.')[-1]  # noqa: N806, F841
                # shutil.copyfile(p, f"{surfMoTmpDir}/EVENT-{simID}.json")
                newEVENT = {}  # noqa: N806
                # load the event file
                with open(p) as f:  # noqa: PTH123
                    EVENT_in_All = json.load(f)  # noqa: N806

                    newEVENT['name'] = EVENT_in_All['Events'][0]['event_id'].replace(
                        'x', '-'
                    )
                    newEVENT['location'] = EVENT_in_All['Events'][0]['location']
                    newEVENT['dT'] = EVENT_in_All['Events'][0]['dT']

                    newEVENT['data_x'] = EVENT_in_All['Events'][0]['timeSeries'][0][
                        'data'
                    ]
                    newEVENT['PGA_x'] = max(newEVENT['data_x'])

                    if (
                        len(EVENT_in_All['Events'][0]['timeSeries']) > 0
                    ):  # two-way shaking
                        newEVENT['data_y'] = EVENT_in_All['Events'][0]['timeSeries'][
                            1
                        ]['data']
                        newEVENT['PGA_y'] = max(newEVENT['data_y'])

                    with open(  # noqa: PTH123
                        f"{surfMoTmpDir}/EVENT-{newEVENT['name']}.json", 'w'
                    ) as outfile:
                        json.dump(newEVENT, outfile)

    return surfaceMoDir


if __name__ == '__main__':
    # Defining the command line arguments

    workflowArgParser = argparse.ArgumentParser(  # noqa: N816
        'Run the NHERI SimCenter workflow for a set of assets.', allow_abbrev=False
    )

    workflowArgParser.add_argument(
        'configuration',
        help='Configuration file specifying the applications and data to be ' 'used',
    )
    workflowArgParser.add_argument(
        '-F',
        '--filter',
        default=None,
        help='Provide a subset of building ids to run',
    )
    workflowArgParser.add_argument(
        '-c', '--check', help='Check the configuration file'
    )
    workflowArgParser.add_argument(
        '-r',
        '--registry',
        default=os.path.join(  # noqa: PTH118
            os.path.dirname(os.path.abspath(__file__)),  # noqa: PTH100, PTH120
            'WorkflowApplications.json',
        ),
        help='Path to file containing registered workflow applications',
    )
    workflowArgParser.add_argument(
        '-f',
        '--forceCleanup',
        action='store_true',
        help='Remove working directories after the simulation is completed.',
    )
    workflowArgParser.add_argument(
        '-d',
        '--referenceDir',
        default=os.path.join(os.getcwd(), 'input_data'),  # noqa: PTH109, PTH118
        help='Relative paths in the config file are referenced to this directory.',
    )
    workflowArgParser.add_argument(
        '-w',
        '--workDir',
        default=os.path.join(os.getcwd(), 'results'),  # noqa: PTH109, PTH118
        help='Absolute path to the working directory.',
    )
    workflowArgParser.add_argument(
        '-a',
        '--appDir',
        default=None,
        help='Absolute path to the local application directory.',
    )
    workflowArgParser.add_argument(
        '-l',
        '--logFile',
        default='log.txt',
        help='Path where the log file will be saved.',
    )

    # Parsing the command line arguments
    wfArgs = workflowArgParser.parse_args()  # noqa: N816

    # update the local app dir with the default - if needed
    if wfArgs.appDir is None:
        workflow_dir = Path(os.path.dirname(os.path.abspath(__file__))).resolve()  # noqa: PTH100, PTH120
        wfArgs.appDir = workflow_dir.parents[1]

    if wfArgs.check:
        run_type = 'set_up'
    else:
        run_type = 'run'

    # Calling the main workflow method and passing the parsed arguments
    main(
        run_type=run_type,
        input_file=wfArgs.configuration,
        app_registry=wfArgs.registry,
        force_cleanup=wfArgs.forceCleanup,
        bldg_id_filter=wfArgs.filter,
        reference_dir=wfArgs.referenceDir,
        working_dir=wfArgs.workDir,
        app_dir=wfArgs.appDir,
        log_file=wfArgs.logFile,
    )
