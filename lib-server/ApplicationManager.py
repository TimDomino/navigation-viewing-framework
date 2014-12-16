#!/usr/bin/python

## @file
# Contains class ApplicationManager.

# import avango-guacamole libraries
import avango
import avango.gua
import avango.daemon
from avango.script import field_has_changed
from examples_common.GuaVE import GuaVE

# import framework libraries
from ConsoleIO import *
from scene_config import scenegraphs

# import client framework libraries
from ClientPortal import *
from View import View

# import python libraries
import os
import subprocess
import time

## global variables which can be retrieved by the whole application ##

## @var APP_all_user_reprsentations
# List of all UserRepresentation instances active in the setup.
APP_all_user_representations = []

## @var APP_all_virtual_display_groups
# List of all VirtualDisplayGroup instances active in the setup.
APP_all_virtual_display_groups = []

## @var APP_all_workspaces
# List of all Workspace instances active in the setup.
APP_all_workspaces = []

## @var APP_current_avatar_mode
# String saying which type of avatars are currently used. Can be "JOSEPH" or "VIDEO"
APP_current_avatar_mode = "JOSEPH"



## Class to build the scenegraph from the Workspaces, Display Groups and Users created.
# Builds a server control monitor for debugging purposes.
class ApplicationManager(avango.script.Script):
  
  ## @var viewer
  # The guacamole viewer to be used for rendering.
  viewer = avango.gua.nodes.Viewer()

  ## @var shell
  # The GuaVE shell to be used when the application is running.
  shell = GuaVE()

  ## @var sf_key1
  # Boolean field representing the key for action 1.
  sf_key1 = avango.SFBool()

  ## @var sf_key2
  # Boolean field representing the key for action 2.
  sf_key2 = avango.SFBool()

  ## @var sf_key3
  # Boolean field representing the key for action 3.
  sf_key3 = avango.SFBool()

  ## @var sf_key4
  # Boolean field representing the key for action 4.
  sf_key4 = avango.SFBool()

  ## Default constructor.
  def __init__(self):
    self.super(ApplicationManager).__init__()

  ## Custom constructor
  # @param WORKSPACE_CONFIG Filepath of the workspace configuration file to be loaded.
  # @param START_CLIENTS Boolean saying if the client processes are to be started automatically.
  def my_constructor(self, WORKSPACE_CONFIG, START_CLIENTS):

    _workspace_config_file_name = WORKSPACE_CONFIG.replace(".py", "")
    _workspace_config_file_name = _workspace_config_file_name.replace("/", ".")
    
    # import workspace configuration file
    __import__(_workspace_config_file_name)
    workspace_config_file_module = sys.modules[_workspace_config_file_name]

    workspaces = workspace_config_file_module.workspaces
    virtual_display_groups = workspace_config_file_module.virtual_display_groups
    
    # parameters
    ## @var background_texture
    # The skymap to be used for all pipelines.
    self.background_texture = "data/textures/sky.jpg"
    avango.gua.create_texture(self.background_texture)

    # references
    ## @var SCENEGRAPH
    # Reference to the scenegraph.
    self.SCENEGRAPH = scenegraphs[0]
    self.viewer.SceneGraphs.value = [self.SCENEGRAPH]

    ## @var NET_TRANS_NODE
    # Reference to the net transformation node.
    self.NET_TRANS_NODE = self.SCENEGRAPH["/net"]

    ## @var start_clients
    # Boolean saying if the client processes are to be started automatically.
    self.start_clients = START_CLIENTS

    # kill all running python processes on display hosts
    if self.start_clients:
      _own_hostname = open('/etc/hostname', 'r').readline().strip(" \n")

      for _workspace in workspaces:
        for _display_group in _workspace.display_groups:
          for _display in _display_group.displays:

            if _display.hostname != _own_hostname:
              _ssh_kill = subprocess.Popen(["ssh", _display.hostname, "killall python3 -9"], universal_newlines=True)


    # viewing setup and start of client processes #

    if START_CLIENTS:

      # get own ip adress
      _server_ip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE, universal_newlines=True).communicate()[0]
      _server_ip = _server_ip.strip(" \n")
      _server_ip = _server_ip.rsplit(" ")
      #_server_ip = str(_server_ip[-1])
      _server_ip = str(_server_ip[0])

      # get own hostname
      _hostname = open('/etc/hostname', 'r').readline()
      _hostname = _hostname.strip(" \n")
      #print(_server_ip, _hostname)

      # get directory name
      _directory_name = os.path.dirname(os.path.dirname(__file__))

    else:
      print_warning("Start of clients disabled for debugging reasons.")

    ## @var workspaces
    # List of all workspace instances loaded from workspace configuration file.
    self.workspaces = workspaces
    APP_all_workspaces = workspaces

    ## @var requestable_navigations
    # Navigation instances which are switchable to by a button press on the device.
    self.requestable_navigations = []

    ## @var requestable_navigations_last_button_states
    # Last button states of the request buttons of requestable navigations to detect changes.
    self.requestable_navigations_last_button_states = []

    ## @var workspace_navigations
    # List of all Navigation instances associated to display groups in a physical workspace.
    # Used for portal teleportation checks.
    self.workspace_navigations = []

    ## @var transit_display_groups
    # List of VirtualDisplayGroup instances that have the transitable flag set true.
    self.transit_display_groups = []

    APP_all_virtual_display_groups = virtual_display_groups


    ## Handle physical viewing setups ##

    for _workspace in self.workspaces:

      _w_id = _workspace.id

      for _display_group in _workspace.display_groups:

        # create proxy geometries
        for _display in _display_group.displays:
          _proxy_geom = _display.create_transformed_proxy_geometry(_workspace, _display_group, _display_group.displays.index(_display))
          scenegraphs[0].Root.value.Children.value.append(_proxy_geom)

        # create 3D video representation in every navigation
        if _workspace.video_3D != None:

          _navigation_count = 0

          for _navigation in _display_group.navigations:

            _workspace.video_3D.create_video_3D_representation_for( "video_w" + str(_workspace.id) + "_dg" + str(_display_group.id) + "_nav" + str(_navigation_count)
                                                                  , _navigation)
            _navigation_count += 1


      # build up user and tool representations
      for _user in _workspace.users:

        _u_id = _user.id

        for _display_group in _workspace.display_groups:

          _dg_id = _display_group.id

          # fill list of requestable navigations
          for _navigation in _display_group.navigations:

            self.workspace_navigations.append(_navigation)

            '''
            if _navigation.is_requestable == True:
              self.requestable_navigations.append( (_workspace, _display_group, _navigation) )
              self.requestable_navigations_last_button_states.append(False)
            '''

          # create view transform node only when free slot is availa
          _view_transform_node = avango.gua.nodes.TransformNode(Name = "w" + str(_w_id) + "_dg" + str(_dg_id) + "_u" + str(_u_id))
          self.NET_TRANS_NODE.Children.value.append(_view_transform_node)

          # create user representation in display group
          _user_repr = _user.create_user_representation_for(_display_group
                                                          , _view_transform_node)
          APP_all_user_representations.append(_user_repr)

          # create tool representation in display_group
          for _tool in _workspace.tools:
            _tool_repr = _tool.create_tool_representation_for(_display_group, _user_repr, False)

            # register portal display groups if this tool representation is a PortalCameraRepresentation
            try:
              _tool_repr.virtual_display_group
              APP_all_virtual_display_groups.append(_tool_repr.virtual_display_group)
            except:
              pass

          for _display in _display_group.displays:

            _s_id = _display_group.displays.index(_display)

            # only add screen node for user when free slot is available
            if _u_id < len(_display.displaystrings):
              _user_repr.add_screen_node_for(_display)
              _user_repr.add_screen_visualization_for(_display)

            else:
              print_warning("Warning: No empty slot left for user " + str(_u_id) + " in workspace " + str(_workspace.name) + " on display " + str(_display.name))
              continue

            # start a client on display host if necessary (and only once)
            if START_CLIENTS and _u_id == 0:

              # start remote ssh shell for remote client processes
              if _hostname != _display.hostname:

                # determine display class, e.g. PhysicalDisplay.LargePowerwall
                _display_class_with_module = _display.__class__.__module__ + "." + _display.__class__.__name__

                # run client process on host
                # start-client.sh SERVER_IP WORKSPACE_ID DISPLAY_GROUP_ID SCREEN_ID DISPLAY_MODULE_NAME.DISPLAY_CLASS NAME
                _ssh_run = subprocess.Popen(["ssh", _display.hostname, _directory_name + \
                "/start-client.sh " + _server_ip + " " + str(_w_id) + " " + \
                str(_dg_id) + " " + str(_s_id) + " " + _display_class_with_module]
                , stderr=subprocess.PIPE, universal_newlines=True)
                time.sleep(1)

              # handle local displays directly by the server application
              else:

                for _index, _displaystring in enumerate(_display.displaystrings):

                  _view = View()
                  _view.my_constructor( self.SCENEGRAPH
                                      , self.viewer
                                      , _display
                                      , _w_id
                                      , _dg_id
                                      , _s_id
                                      , _index)

                ## TODO: Initialize ClientPortalManger (only once) when local displays
                ##       are present.
                ##       portal_manager = ClientPortalManager()
                ##       portal_manager.my_constructor(self.SCENEGRAPH, some sort of view list)





    ## Handle virtual viewing setups ##

    _virtual_user_representations = []

    for _display_group in APP_all_virtual_display_groups:

      _display_group.add_virtual_display_nodes()
      _transit_entry_added = False
      _virtual_user_representations_of_dg = []

      # create user representations
      for _physical_user_repr in APP_all_user_representations:

        _complex = True
        if _display_group.viewing_mode == "2D":
          _complex = False

        _virtual_user_repr = _physical_user_repr.USER.create_user_representation_for(
                             _display_group
                           , _display_group.exit_node
                           , 'head_' + _physical_user_repr.view_transform_node.Name.value
                           , _complex)

        _virtual_user_repr.add_dependent_node(_physical_user_repr.head)

        # add screen nodes to user representation
        for _screen in _display_group.screen_nodes:
          _virtual_user_repr.add_existing_screen_node(_screen)

        _virtual_user_representations.append(_virtual_user_repr)
        _virtual_user_representations_of_dg.append(_virtual_user_repr)

        # collect transit portals
        if _display_group.transitable and _transit_entry_added == False:
          
          # add tuple of (display_group, one_virtual_user_repr)
          # one user representation is needed to capture the connected navigation
          self.transit_display_groups.append( (_display_group, _virtual_user_repr) )
          _transit_entry_added = True


        for _workspace in self.workspaces:
          for _tool in _workspace.tools:

            _w_id = _workspace.id
            _t_id = _tool.id

            # jump over PortalCameraRepresentations
            try:
              _tool.captured_shots
              continue
            except:
              pass

            # jump over tools outside the workspace of the currently handled physical user representation
            if _tool.WORKSPACE_INSTANCE == _physical_user_repr.USER.WORKSPACE_INSTANCE:

              #print("Create tool representation for", _tool)

              _virtual_tool_repr = _tool.create_tool_representation_for(_display_group, _virtual_user_repr, True)

              # find physical tool representation for the tool transform node
              for _child in _physical_user_repr.view_transform_node.Children.value:
                if _child.Name.value == "tool_" + str(_t_id):
                  _virtual_tool_repr.add_dependent_node(_child)
                  break

            
    for _virtual_user_representation in _virtual_user_representations:
      APP_all_user_representations.append(_virtual_user_representation)


    ## Initialize group names ##

    # physical and virtual workspaces
    for _workspace in self.workspaces:

      for _display_group in _workspace.display_groups:

        # trigger correct group names of navigation trace
        for _nav in _display_group.navigations:
          _nav.handle_correct_visibility_groups()

        # trigger correct groups for all users at display
        for _user in _workspace.users:
          _user.handle_correct_visibility_groups_for(_display_group)

          for _portal_display_group in APP_all_virtual_display_groups:
            _user.handle_correct_visibility_groups_for(_portal_display_group)

    # connect proper navigations
    for _user_representation in APP_all_user_representations:
      _user_representation.connect_navigation_of_display_group(0)

    # video 3D group names (after users were assigned to navigations)
    for _workspace in self.workspaces:

      if _workspace.video_3D != None:

        for _display_group in _workspace.display_groups:
          for _nav in _display_group.navigations:

            _workspace.video_3D.handle_correct_visibility_groups_for(_nav)

    ## Keyboard Sensor Setup ##

    self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
    self.keyboard_sensor.Station.value = "device-keyboard0"

    self.sf_key1.connect_from(self.keyboard_sensor.Button19) # key F1
    self.sf_key2.connect_from(self.keyboard_sensor.Button20) # key F2
    self.sf_key3.connect_from(self.keyboard_sensor.Button21) # key F3
    self.sf_key4.connect_from(self.keyboard_sensor.Button22) # key F4

    # set evaluation policy
    self.always_evaluate(True)

  ## Called whenever sf_key1 changes.
  @field_has_changed(sf_key1)
  def sf_key1_changed(self):

    if self.sf_key1.value == True:

      video_visibility_table = {
                            "dlp_wall"  : {"table" : False, "lcd_wall" : False, "portal" : False}
                          , "table" : {"dlp_wall" : False, "lcd_wall" : False, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : False,  "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : False, "table" : False, "lcd_wall" : False} 
                                }

      avatar_visibility_table = {
                            "dlp_wall"  : {"table" : False, "lcd_wall" : True, "portal" : False}
                          , "table" : {"dlp_wall" : True, "lcd_wall" : True, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : True,  "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : True, "table" : False, "lcd_wall" : True} 
                          }

      tool_visibility_table = {
                            "dlp_wall"  : {"table" : False, "portal" : False}
                          , "table" : {"dlp_wall" : True, "portal" : False}  
                          , "lcd_wall" : {"dlp_wall" : True, "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : True, "table" : False, "lcd_wall" : True, "portal" : False}
                              }

      for _workspace in APP_all_workspaces:

        for _user in _workspace.users:
          _user.change_visiblity_table(avatar_visibility_table)
        
        if _workspace.video_3D != None:
          _workspace.video_3D.change_visiblity_table(video_visibility_table)

      for _tool in APP_all_workspaces[0].tools:
       _tool.change_visiblity_table(tool_visibility_table)
      
      print_message("Visibility tables in workspace 0 changed: table tool representations invisible on walls.")

  ## Called whenever sf_key2 changes.
  @field_has_changed(sf_key2)
  def sf_key2_changed(self):

    if self.sf_key2.value == True:

      video_visibility_table = {
                            "dlp_wall"  : {"table" : False, "lcd_wall" : False, "portal" : False}
                          , "table" : {"dlp_wall" : False, "lcd_wall" : False, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : False,  "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : False, "table" : False, "lcd_wall" : False} 
                                }

      avatar_visibility_table = {
                            "dlp_wall"  : {"table" : True, "lcd_wall" : True, "portal" : False}
                          , "table" : {"dlp_wall" : True, "lcd_wall" : True, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : True,  "table" : True, "portal" : False}
                          , "portal" : {"dlp_wall" : True, "table" : True, "lcd_wall" : True} 
                          }

      tool_visibility_table = {
                            "dlp_wall"  : {"table" : True, "portal" : False}
                          , "table" : {"dlp_wall" : True, "portal" : False}  
                          , "lcd_wall" : {"dlp_wall" : True, "table" : True, "portal" : False}
                          , "portal" : {"dlp_wall" : True, "table" : False, "lcd_wall" : True, "portal" : False}
                              }

      for _workspace in APP_all_workspaces:

        for _user in _workspace.users:
          _user.change_visiblity_table(avatar_visibility_table)
        
        if _workspace.video_3D != None:
          _workspace.video_3D.change_visiblity_table(video_visibility_table)

      for _tool in APP_all_workspaces[0].tools:
       _tool.change_visiblity_table(tool_visibility_table)
      
      print_message("Visibility tables in workspace 0 changed: table tool and user representations visible on walls.")

  ## Called whenever sf_key3 changes.
  @field_has_changed(sf_key3)
  def sf_key3_changed(self):

    if self.sf_key3.value == True:

      APP_current_avatar_mode = "VIDEO"

      avatar_visibility_table = {
                            "dlp_wall"  : {"table" : False, "lcd_wall" : False, "portal" : False}
                          , "table" : {"dlp_wall" : False, "lcd_wall" : False, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : False,  "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : False, "table" : False, "lcd_wall" : False} 
                                }

      video_visibility_table = {
                            "dlp_wall"  : {"table" : False, "lcd_wall" : True, "portal" : False}
                          , "table" : {"dlp_wall" : True, "lcd_wall" : True, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : True,  "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : True, "table" : False, "lcd_wall" : True} 
                          }

      for _workspace in APP_all_workspaces:
        if _workspace.video_3D != None:

          for _user in _workspace.users:
            _user.change_visiblity_table(avatar_visibility_table)
          
          _workspace.video_3D.change_visiblity_table(video_visibility_table)
      
      print_message("Video avatars enabled.")

  ## Called whenever sf_key4 changes.
  @field_has_changed(sf_key4)
  def sf_key4_changed(self):

    if self.sf_key4.value == True:

      APP_current_avatar_mode = "JOSEPH"

      video_visibility_table = {
                            "dlp_wall"  : {"table" : False, "lcd_wall" : False, "portal" : False}
                          , "table" : {"dlp_wall" : False, "lcd_wall" : False, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : False,  "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : False, "table" : False, "lcd_wall" : False} 
                                }

      avatar_visibility_table = {
                            "dlp_wall"  : {"table" : False, "lcd_wall" : True, "portal" : False}
                          , "table" : {"dlp_wall" : True, "lcd_wall" : True, "portal" : False}
                          , "lcd_wall" : {"dlp_wall" : True,  "table" : False, "portal" : False}
                          , "portal" : {"dlp_wall" : True, "table" : False, "lcd_wall" : True} 
                          }

      for _workspace in APP_all_workspaces:
        if _workspace.video_3D != None:

          for _user in _workspace.users:
            _user.change_visiblity_table(avatar_visibility_table)
          
          _workspace.video_3D.change_visiblity_table(video_visibility_table)
      
      print_message("Joseph avatars enabled.")

  ## Evaluated every frame.
  def evaluate(self):

    ## handle portal transitions ##

    for _nav in self.workspace_navigations:

      # if navigation does not allow portal transit, go to next loop iteration
      if _nav.reacts_on_portal_transit == False:
        continue

      # if navigation has no device (e.g. static navigation), do not allow transit
      try:
        _nav.device
      except:
        continue

      _nav_device_mat = _nav.sf_platform_mat.value * \
                        avango.gua.make_trans_mat(_nav.device.sf_station_mat.value.get_translate())


      _nav_device_pos = _nav_device_mat.get_translate()

      _nav_device_pos2 = _nav_device_mat * avango.gua.Vec3(0.0,0.0,1.0)
      _nav_device_pos2 = avango.gua.Vec3(_nav_device_pos2.x, _nav_device_pos2.y, _nav_device_pos2.z)

      '''
      for _tuple in self.transit_display_groups:

        _portal_display_group = _tuple[0]
        _first_virtual_user_repr = _tuple[1]

        # only allow teleportation when in 3D mode
        if _portal_display_group.viewing_mode != "3D":
          continue

        # check for transit in every single virtual display
        for _display in _portal_display_group.displays:

          _index = _portal_display_group.displays.index(_display)

          _active_navigation = _portal_display_group.navigations[_first_virtual_user_repr.connected_navigation_id]
          _mat = avango.gua.make_inverse_mat(_portal_display_group.entry_node.Transform.value * _portal_display_group.screen_nodes[_index].Transform.value)

          _nav_device_portal_space_mat = _mat * _nav_device_mat
          _nav_device_portal_space_pos = _mat * _nav_device_pos
          _nav_device_portal_space_pos2 = _mat * _nav_device_pos2
          _nav_device_portal_space_pos = avango.gua.Vec3(_nav_device_portal_space_pos.x, _nav_device_portal_space_pos.y, _nav_device_portal_space_pos.z)

          # do a teleportation if navigation enters portal
          if  _nav_device_portal_space_pos.x > -_display.size[0]/2     and \
              _nav_device_portal_space_pos.x <  _display.size[0]/2     and \
              _nav_device_portal_space_pos.y > -_display.size[1]/2     and \
              _nav_device_portal_space_pos.y <  _display.size[1]/2     and \
              _nav_device_portal_space_pos.z < 0.0                    and \
              _nav_device_portal_space_pos2.z >= 0.0:

            _nav.inputmapping.set_abs_mat(avango.gua.make_trans_mat(_portal_display_group.screen_nodes[_index].Transform.value.get_translate()) * \
                                          _active_navigation.sf_abs_mat.value * \
                                          avango.gua.make_rot_mat(_portal_display_group.screen_nodes[_index].Transform.value.get_rotate()) * \
                                          avango.gua.make_scale_mat(_active_navigation.sf_scale.value) * \
                                          avango.gua.make_trans_mat(_nav_device_portal_space_pos) * \
                                          avango.gua.make_rot_mat(_nav_device_portal_space_mat.get_rotate_scale_corrected()) * \
                                          avango.gua.make_trans_mat(_nav.device.sf_station_mat.value.get_translate() * -1.0) * \
                                          avango.gua.make_inverse_mat(avango.gua.make_scale_mat(_active_navigation.sf_scale.value)))

            if _nav.trace != None:
              _nav.trace.clear(_nav.inputmapping.sf_abs_mat.value)
            
            _nav.inputmapping.scale_stop_time = None
            _nav.inputmapping.set_scale(_active_navigation.sf_scale.value, False)
      '''

    '''
    ## handle requestable navigations ##

    for _requestable_nav in self.requestable_navigations:

      _workspace = _requestable_nav[0]
      _display_group = _requestable_nav[1]
      _navigation = _requestable_nav[2]
      _requestable_nav_index = self.requestable_navigations.index(_requestable_nav)
      _last_button_state = self.requestable_navigations_last_button_states[_requestable_nav_index]

      # if button change from negative to positive, trigger action
      #print(_navigation.sf_request_trigger.value)

      if _navigation.sf_request_trigger.value == True and \
         _last_button_state == False:

        self.requestable_navigations_last_button_states[_requestable_nav_index] = True

        # trigger coupling
        if _navigation.active_user_representations == []:
          
          _users_in_range = _workspace.get_all_users_in_range(avango.gua.make_inverse_mat(_display_group.offset_to_workspace) * _navigation.device.tracking_reader.sf_abs_vec.value, 0.8)

          for _user in _users_in_range:
            self.switch_navigation_for(_workspace.id, _display_group.id, _user.id, _display_group.navigations.index(_navigation))

        # reset coupling
        else:

          # get user ids to be reset to navigation 0
          _active_user_ids = []

          for _user_repr in _navigation.active_user_representations:
            _active_user_ids.append(_user_repr.USER.id)

          # switch navigation for 
          for _user_id in _active_user_ids:
            self.switch_navigation_for(_workspace.id, _display_group.id, _user_id, 0)

      # if button change from positive to negative, reset flag
      elif _navigation.sf_request_trigger.value == False and \
           _last_button_state == True:

        self.requestable_navigations_last_button_states[_requestable_nav_index] = False
  '''

  ## Initializes the GroupNames field of all UserRepresentation's avatars.
  # Users cannot see the avatars in own display group, but the ones in others.
  def init_avatar_group_names(self):

    for _user_repr_1 in APP_all_user_representations:

      for _user_repr_2 in APP_all_user_representations:

        if _user_repr_2.DISPLAY_GROUP != _user_repr_1.DISPLAY_GROUP:

          _user_repr_1.append_to_avatar_group_names(_user_repr_2.view_transform_node.Name.value)
  

  ## Switches the navigation for a user at a display group. 
  # @param WORKSPACE_ID The workspace id in which the user is active.
  # @param DISPLAY_GROUP_ID The display group id to change the navigation for.
  # @param USER_ID The user id to change the navigation for.
  # @param NAVIGATION_ID The navigation id to change to.
  def switch_navigation_for(self, WORKSPACE_ID, DISPLAY_GROUP_ID, USER_ID, NAVIGATION_ID):

    _user_instance = self.workspaces[WORKSPACE_ID].users[USER_ID]
    _user_instance.switch_navigation_at_display_group(DISPLAY_GROUP_ID, NAVIGATION_ID, self.workspaces[WORKSPACE_ID].users)

  ## Starts the shell and the viewer.
  # @param LOCALS Local variables.
  # @param GLOBALS Global variables.
  def run(self, LOCALS, GLOBALS):
    self.shell.start(LOCALS, GLOBALS)
    self.viewer.run()

  ## Lists the variables of the shell.
  def list_variables(self):
    self.shell.list_variables()
