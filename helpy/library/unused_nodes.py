from ..procedure import Procedure
from ..config import *
from .. import SVG
import maya.cmds as cmds
import maya.mel as mel

# this class function manually translated from Maya's MEL file.
# script resources file: MLdeleteUnused.mel and deleteIfNotReferenced.mel might be found in C:\Program Files\Autodesk\Maya2020\scripts\others

# MAYA BUG?: sometimes during delete unused nodes, this MEL function still left some unused behind, 
# so there might be case where user need to click delete unused nodes twice
# not sure if this is by design from the maya dev team..
#
# TEMP FIX: for temporary fix can refer to comment below with "# FIX", that will add all material in scene to cleanup but will make it a bit heavier

@register_procedure(":cube.png")
class UnusedNodesProcedure(Procedure):
    NAME = "Unused Nodes"

    def __init__(self):
        super(UnusedNodesProcedure, self).__init__()

    def get_render_nodes(self): # render nodes include utility nodes, need to remember this
        render_types = cmds.listNodeTypes("texture") + cmds.listNodeTypes("utility") + cmds.listNodeTypes("imageplane") + cmds.listNodeTypes("shader")
        render_nodes = cmds.ls(type=render_types, long=True)
        mr_nodes = cmds.lsThroughFilter("DefaultMrNodesFilter") or []
        render_nodes.extend(mr_nodes)
        return list(set(render_nodes))

    def delete_if_not_referenced(self, nodeToDelete):
        if nodeToDelete and cmds.objExists(nodeToDelete) and not cmds.referenceQuery(nodeToDelete, isNodeReferenced=True):
            isLocked = cmds.lockNode(nodeToDelete, q=True, lock=True)[0]
            if not isLocked:
                mel.eval('evalEcho("delete %s")'%nodeToDelete)
                return True
        return False

    def is_shading_group_unused(self, shading_grp):
        if not cmds.objExists(shading_grp): 
            return False

        if cmds.sets(shading_grp, q=True, renderable=True):
            defaults = ["initialShadingGroup", "initialParticleSE", "defaultLightSet", "defaultObjectSet"]
            if shading_grp in defaults: 
                return False
            
            objs = cmds.sets(shading_grp, q=True) or [] #cmds.sets returns non if empty
            layers= cmds.listConnections(shading_grp, type="renderLayer") or []

            if not objs and not layers: 
                return True
            else:
                connected = False
                attrs = [".surfaceShader", ".volumeShader", ".displacementShader"]

                for attr in attrs:
                    connection = cmds.listConnections(shading_grp + attr) or []
                    if connection:
                        connected = True
                        break
                if not connected:
                    cmd = 'callbacks -executeCallbacks -hook "allConnectedShaders" "%s"'%shading_grp    # remember to use double tick as arguments in MEL
                    custom_shaders = mel.eval(cmd) or []

                    for shader in custom_shaders:
                        if shader != "":
                            connected = True
                            break
                if not connected:
                    return True
        return False

    def find_empty_shading_groups(self):
        unused_shading_groups = []
        all_sets = cmds.ls(sets=True)

        for current_shading_group in all_sets:
            should_delete = False
            if self.is_shading_group_unused(current_shading_group):
                should_delete = True

                # give plugins chance to label node as "shouldnt be deleted"
                conn = cmds.listConnections(current_shading_group, shapes=True, connections=True, source=False) or []
                for j in range(0, len(conn), 2):
                    dest_plug = conn[j]
                    source_node = conn[j+1]

                    cmd = 'callbacks -executeCallbacks -hook "preventMaterialDeletionFromCleanUpSceneCommand" "%s" "%s" "%s"'%(current_shading_group, source_node, dest_plug) # remember to use double tick as arguments in MEL
                    prevent_result = mel.eval(cmd) or []

                    if any(prevent_result):
                        should_delete = False
                        break
                    
            if should_delete:
                unused_shading_groups.append(current_shading_group)

        return unused_shading_groups
    
    def find_unused_materials_node(self):
        unused_material_nodes = []
        default_materials = cmds.ls(defaultNodes=True, materials=True)
        all_materials = cmds.ls(long=True, mat=True)

        for currShader in all_materials:
            # if default material just skip it
            if currShader in default_materials:
                continue

            conn = cmds.listConnections(currShader, shapes=True, connections=True, source=False) or []
            for i in range(0, len(conn), 2):
                local_plug = conn[i]
                dest_node = conn[i+1]
            
                if local_plug != currShader + ".message":
                    should_delete = False
                    break
                else:
                    shading_engine_conns = cmds.listConnections(local_plug, type="shadingEngine") or []
                    cmd = 'callbacks -executeCallbacks -hook "preventMaterialDeletionFromCleanUpSceneCommand" "%s" "%s" "%s"'%(currShader, conn[i+1], conn[i])
                    thirdPartyPreventDeletionsList = mel.eval(cmd) or []
                    thirdPartyPreventDeletion = any(thirdPartyPreventDeletionsList)

                    if shading_engine_conns:
                        should_delete = False
                        break
                    elif thirdPartyPreventDeletion:
                        should_delete = False
                        break
                    else:
                         should_delete = True
            
            if should_delete:
                unused_material_nodes.append(currShader)
        
        return unused_material_nodes

    def find_unused_texture_or_utility_nodes(self):
        # on checking texture, postprocess or utility node, node will be ignored if message attr connect to one of these item below 
        unused_node_list = []
        special_destination_attr = ["shadingEngine", "imagePlane", "arrayMapper", "directionalLight", "spotLight", "pointLight", "areaLight", "transform"] 
        default_materials = cmds.ls(defaultNodes=True, materials=True)

        for node in self.get_render_nodes():    # FIX: add > cmds.ls(long=True, mat=True)  
            if node in default_materials or not cmds.objExists(node):
                continue

            node_type = cmds.nodeType(node)
            if node_type == "heightField":
                if cmds.listConnections(node, connections=True, source=True, shapes=True): 
                    continue
            if node_type == "imagePlane":
                if cmds.getAttr(node + ".lockedToCamera") == 0:
                    continue

            should_delete = True
            conn = cmds.listConnections(node, connections=True, source=False, shapes=True) or []

            for j in range(0, len(conn), 2):
                local_plug = conn[j]
                dest_node = conn[j+1]

                if local_plug.endswith(".message"):
                    connType = cmds.nodeType(dest_node)
                    if connType in special_destination_attr or cmds.objectType(dest_node, isa="camera"):
                        should_delete = False
                        break

                    is_shader = any([
                            mel.eval('isClassified "%s" "shader/surface"'%dest_node),
                            mel.eval('isClassified "%s" "shader/volume"'%dest_node),
                            mel.eval('isClassified "%s" "shader/displacement"'%dest_node),
                        ])
                    
                    if is_shader:
                        should_delete = False
                        break
                    
                    # give plugins a chance to label the node as 'shouldnt be deleted'
                    cmd = 'callbacks -executeCallbacks -hook "preventMaterialDeletionFromCleanUpSceneCommand" "%s" "%s" "%s"'%(node, dest_node, local_plug)
                    thirdPartyPreventDeletionsList = mel.eval(cmd) or []
                    thirdPartyPreventDeletion = any(thirdPartyPreventDeletionsList)

                    if thirdPartyPreventDeletion:
                        should_delete = False
                        break
                
                else:
                    should_delete = False
                    break

            if should_delete:
                unused_node_list.append(node)

        return unused_node_list
    
    def delete_unused_texture_or_utility_nodes(self):
        # on checking texture, postprocess or utility node, node will be ignored if message attr connect to one of these item below 
        deleteAnything = True
        while deleteAnything:
            unused = self.find_unused_texture_or_utility_nodes()
            if unused:
                for node in unused:
                    self.delete_if_not_referenced(node)
                deleteAnything=True
            else:
                deleteAnything=False

    def print_list(self, title="TITLE", _list=[]):
        print("")
        print(title)
        print("=====================================")
        print("List > ", _list)
        for i in _list:
            print(i)
        print("")

    # --- checkers ---

    @checker(0, "found empty shading groups")
    def found_empty_shading_groups(self):
        if self.find_empty_shading_groups():
            return self.FAILED
        else:
            return self.FINISHED
        
    @checker(1, "found unused material nodes")
    def found_unused_material_nodes(self):
        if self.find_unused_materials_node():
            return self.FAILED
        else:
            return self.FINISHED
        
    @checker(2, "found unused texture/utility nodes")
    def found_unused_texture_or_utility_nodes(self):
        if self.find_unused_texture_or_utility_nodes():
            return self.FAILED
        else:
            return self.FINISHED

    # --- unused shading groups helpers ---

    @helper([0], "print unused shading groups", ":textBeam.png")
    def print_unused_shading_groups(self):
        self.print_list("UNUSED SHADING GROUPS", self.find_empty_shading_groups())

    # unused material helpers

    @helper([1], "print unused material", ":textBeam.png")
    def print_unused_material(self):
        self.print_list("UNUSED MATERIAL", self.find_unused_materials_node())

    @helper([1], "select unused material", SVG.RENDERED["cursor"])
    def select_unused_material(self):
        cmds.select(self.find_unused_materials_node())

    # --- unused texture/utility helpers ---

    @helper([2], "print unused texture/utility nodes", ":textBeam.png")
    def print_unused_texture_or_utility(self):
        self.print_list("UNUSED TEXTURE/UTILITY NODDES", self.find_unused_texture_or_utility_nodes())

    @helper([2], "select unused texture/utility nodes", SVG.RENDERED["cursor"])
    def select_unused_texture_or_utility(self):
        cmds.select(self.find_unused_texture_or_utility_nodes())

    # --- global helpers ---
    
    @helper([0,1,2], "delete unused nodes", ":delete.png")
    def delete_unused_nodes(self):
        # we need to make sure line below in correct sequence, according to MEL.
        # main reason, at first glance, material might looks used until we delete any unused shading group 
        # same with utility that connected to unused material nodes
        for sg in self.find_empty_shading_groups():
            self.delete_if_not_referenced(sg)
        for material in  self.find_unused_materials_node():
            self.delete_if_not_referenced(material)
        self.delete_unused_texture_or_utility_nodes()