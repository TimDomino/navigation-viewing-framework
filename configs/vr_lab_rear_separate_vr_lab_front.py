#!/usr/bin/python

## @file
# Contains workspace, navigation, display group and user configuration classes to be used by the framework.

# import guacamole libraries
import avango
import avango.gua

# import framework libraries
from Workspace import Workspace
from SteeringNavigation import SteeringNavigation
from display_config import *

## Create Workspaces first ##
vr_lab_rear = Workspace('VR-Lab-Rear', avango.gua.make_trans_mat(0.0, 0.043, 1.6))
vr_lab_front = Workspace('VR-Lab-Front', avango.gua.make_trans_mat(0.0, 0.043, 1.6))

## Create Navigation instances ##
spheron_navigation = SteeringNavigation()
spheron_navigation.my_constructor( STARTING_MATRIX = avango.gua.make_trans_mat(0, 0, 0) * \
                                                     avango.gua.make_rot_mat(0, 0, 1, 0)
                                 , STARTING_SCALE = 1.0
                                 , INPUT_DEVICE_TYPE = 'NewSpheron'
                                 , INPUT_DEVICE_NAME = 'device-new-spheron'
                                 , NO_TRACKING_MAT = avango.gua.make_trans_mat(0.0, 1.75, 1.6)
                                 , GROUND_FOLLOWING_SETTINGS = [True, 0.75]
                                 , MOVEMENT_TRACES = False
                                 , INVERT = False
                                 , TRANSMITTER_OFFSET = avango.gua.make_trans_mat(0.0, 0.043, 1.6)
                                 , AVATAR_TYPE = 'joseph'
                                 , DEVICE_TRACKING_NAME = 'tracking-new-spheron')

spacemouse_navigation = SteeringNavigation()
spacemouse_navigation.my_constructor( STARTING_MATRIX = avango.gua.make_trans_mat(0, 0, 20) * \
                                                        avango.gua.make_rot_mat(0, 0, 1, 0)
                                    , STARTING_SCALE = 50.0
                                    , INPUT_DEVICE_TYPE = 'Spacemouse'
                                    , INPUT_DEVICE_NAME = 'device-spacemouse'
                                    , NO_TRACKING_MAT = avango.gua.make_trans_mat(0.0, 0.0, 0.0)
                                    , GROUND_FOLLOWING_SETTINGS = [False, 0.75]
                                    , MOVEMENT_TRACES = False
                                    , INVERT = True
                                    , TRANSMITTER_OFFSET = avango.gua.make_trans_mat(0.73, -0.9, 1.97) * \
                                                           avango.gua.make_rot_mat(-90, 0, 1, 0)
                                    , AVATAR_TYPE = 'joseph'
                                    , DEVICE_TRACKING_NAME = None)

old_spheron_navigation = SteeringNavigation()
old_spheron_navigation.my_constructor( STARTING_MATRIX = avango.gua.make_trans_mat(0, 0, 0)
                                     , STARTING_SCALE = 1.0
                                     , INPUT_DEVICE_TYPE = 'OldSpheron'
                                     , INPUT_DEVICE_NAME = 'device-old-spheron'
                                     , NO_TRACKING_MAT = avango.gua.make_trans_mat(0.0, 1.75, 1.6)
                                     , GROUND_FOLLOWING_SETTINGS = [True, 0.75]
                                     , MOVEMENT_TRACES = False
                                     , INVERT = False
                                     , TRANSMITTER_OFFSET = avango.gua.make_trans_mat(0.0, 0.043, 1.6)
                                     , AVATAR_TYPE = 'joseph'
                                     , DEVICE_TRACKING_NAME = 'tracking-old-spheron')

## Create display groups ##
vr_lab_rear.create_display_group( DISPLAY_LIST = [large_powerwall]
                                , NAVIGATION_LIST = [spheron_navigation])

vr_lab_rear.create_display_group( DISPLAY_LIST = [touch_table_3D]
                                , NAVIGATION_LIST = [spacemouse_navigation])

vr_lab_front.create_display_group(DISPLAY_LIST = [small_powerwall]
                                , NAVIGATION_LIST = [old_spheron_navigation])

## Create users ##
vr_lab_rear.create_user( VIP = False
                       , GLASSES_ID = 1
                       , HEADTRACKING_TARGET_NAME = 'tracking-dlp-glasses-1'
                       , EYE_DISTANCE = 0.065)

vr_lab_rear.create_user( VIP = False
                       , GLASSES_ID = 4
                       , HEADTRACKING_TARGET_NAME = 'tracking-dlp-glasses-4'
                       , EYE_DISTANCE = 0.065)

vr_lab_rear.create_user( VIP = False
                       , GLASSES_ID = 5
                       , HEADTRACKING_TARGET_NAME = 'tracking-dlp-glasses-5'
                       , EYE_DISTANCE = 0.065)

vr_lab_rear.create_user( VIP = False
                       , GLASSES_ID = 6
                       , HEADTRACKING_TARGET_NAME = 'tracking-dlp-glasses-6'
                       , EYE_DISTANCE = 0.065)

vr_lab_front.create_user(VIP = False
                       , GLASSES_ID = None
                       , HEADTRACKING_TARGET_NAME = 'tracking-lcd-glasses-1'
                       , EYE_DISTANCE = 0.065)


## Store all used workspaces in a list ##
workspaces = [
  vr_lab_rear,
  vr_lab_front

  ]