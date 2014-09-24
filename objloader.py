import math
import sys

from collections import defaultdict
from OpenGL.GL import *

def normalize_vertex_array(verts):
    """ Uniformly rescale 3D vertex data so that its axis of
        greatest change is normalized to the range [0,1]

        Original input is modified
    """

    # Set initial min/max values to their inverse extremes so
    # the loop below will change their values no matter what.
    v_max = [sys.float_info.min] * 3
    v_min = [sys.float_info.max] * 3
    for v in verts:
        for i in range(0,3):
            if v[i] > v_max[i]:
                v_max[i] = v[i]
            if v[i] <v_min[i]:
                v_min[i] = v[i]

    # Generate statistical mean
    mean = [a+b for a,b in zip(v_max,v_min)]
    mean = [a/2.0 for a in mean]

    # translate vertices 
    for v in verts:
        for i in range(0,3):
            v[i] -= mean[i]

    v_max = [a+b for a,b in zip(v_max,mean)]
    v_min = [a+b for a,b in zip(v_min,mean)]
    
    global g_Translate
    rad = math.fabs(max(v_max) - min(v_min))
    #g_Translate[2] = -rad 
    return verts

def normalize_vertex_array(verts):
    """ Uniformly rescale 3D vertex data so that its axis of
        greatest change is normalized to the range [0,1]

        Original input is unmodified
    """
    new_verts = list(verts)
    normalize_vertex_array(new_vert)
    return new_verts

def parse_vertex_line(tokens):
    """ Parse Wavefront OBJ Vertex line

        Input:
            tokens - Array of vertex line tokens as strings
                Format1: ['v','1','2','3']
                Format2: ['v','1','2','3','4','5','6']
    """
    size = len(tokens)

    # valid vertex strings are either v x y z or v x y z r g b (Meshlab dumps color to vertices)
    # TODO: Look in to meshlab's output to find out if their color format is right.
    if not (size == 7 or size == 4): return None
    if not (tokens[0] in ['v','V']): return None

    # x/y/z values will *always* be the first values after the line identifier
    xyz = tokens[1:4]

    return [float(xyz[0]),float(xyz[1]),float(xyz[2])]

def parse_uv_line(tokens):
    """ Parse Wavefront OBJ UV line

        Input:
            tokens - Array of UV line tokens as strings
                Format: ['vt','0.4','0.5']
    """

    size = len(tokens)

    # valid uv strings are 'vt 0.1 0.1'
    if not (size == 3): return None
    if not (tokens[0] in ['vt','VT']): return None

    # x/y/z values will *always* be the first values after the line identifier
    uv = tokens[1:3]

    return [float(uv[0]),float(uv[1])]

def parse_face_line(tokens):
    """ Parse Wavefront OBJ face line

        Input:
            tokens - Array of face line tokens as strings
                Format1: ['f','1','2','3']
                Format2: ['f','1//1','2//2','3//3']
                Format3: ['f','1/1/1','2/2/2','3/3/3']
        Output:
            face - Single triangluar face.
                Format: [corner_a,corner_b,corner_c,uv_a,uv_b,uv_c,normal_a,normal_b,normal_c]
    """

    size = len(tokens)

    # Currently this method only supports triangulated mesh data
    if not (size == 4): return None
    if not (tokens[0] in ['f','F']): return None

    # face index values will *always* be the first values after the line identifier
    fs = tokens[1:4]

    f1 = fs[0].split('/')
    f2 = fs[1].split('/')
    f3 = fs[2].split('/')

    a1 = int(f1[0]) if f1[0] != '' else None
    b1 = int(f1[1]) if f1[1] != '' else None
    c1 = int(f1[2]) if f1[2] != '' else None
    
    a2 = int(f2[0]) if f2[0] != '' else None
    b2 = int(f2[1]) if f2[1] != '' else None
    c2 = int(f2[2]) if f2[2] != '' else None
        
    a3 = int(f3[0]) if f3[0] != '' else None
    b3 = int(f3[1]) if f3[1] != '' else None
    c3 = int(f3[2]) if f3[2] != '' else None
    # Wavefront .obj stores faces in one-based numbering, subtract 1
    # from each index to properly index vertex array
    return[a1,a2,a3,b1,b2,b3,c1,c2,c3]



def load(file_name,normalize=False):
    obj_line_parsers = defaultdict(lambda : lambda a: None,{
        'v':parse_vertex_line,
        'V':parse_vertex_line,
        'f':parse_face_line,
        'F':parse_face_line,
        'vt':parse_uv_line,
    })
    obj_parse_assignment = defaultdict(lambda : lambda a: None,{
        'v':lambda b:verts.append(b),
        'V':lambda b:verts.append(b),
        'f':lambda b:faces.append(b),
        'F':lambda b:faces.append(b),
        'vt':lambda b:uvs.append(b)
    })

    verts = []
    colors = None
    faces = []
    norms = []
    uvs = []

    with open(file_name,'r') as fr:
        for line_index,line in enumerate(fr):
            # tokenize each line (ie. Split lines up in to lists of elements)
            # e.g. f 1//1 2//2 3//3 => [f,1//1,2//2,3//3]
            tokens = line.strip().split(' ')
            if tokens == None: continue
            if tokens[0] == '': continue

            try:
                key = tokens[0]
                value = obj_line_parsers[key](tokens)
                obj_parse_assignment[key](value)
            except Exception, err:
                print "Ill formed line[%d]: %s"%(line_index,line)
                print "Err: ",err
      
    if normalize:
        verts = normalize_obj(verts)

    return verts,faces,uvs,norms,colors

def process_obj(verts,faces,uvs,normals,colors):
    """ Split 6-component facial data in to individual triangles
        for OpenGL

        Note:  Vertex indices are not used directly by OpenGL.
        They are used here to create single, large, vertex array
        grouped by triangle.  This means each very will likely
        be used several times.
    """
    # Faces currently store 6 values, split them up a bit
    out_verts = []
    out_uvs = []
    for face in faces:
        out_verts.append(verts[face[0]-1])
        out_verts.append(verts[face[1]-1])
        out_verts.append(verts[face[2]-1])

        out_uvs.append(uvs[face[3]-1])
        out_uvs.append(uvs[face[4]-1])
        out_uvs.append(uvs[face[5]-1])

    return out_verts,out_uvs

def generate_2d_ctypes(data):
    """ Covert 2D Python list of lists to 2D ctype array

        Input:
            data - 2D array like vertices[36][3]
                Format: array[rows][cols] where rows are individual elements
                and cols are components of each element.  
    """
    c = len(data[0])
    r = len(data)

    # multidimensional ctype arrays require parens
    # or the array type below would become float[r*c]
    # instead of float[r][c].  Alternative notation: 
    # array_type = GLfloat*c*r
    array_type = r * (c*GLfloat)
    ret = array_type()

    for i in range(0,len(data)):
        for j in range(0,c):
            ret[i][j] = data[i][j]

    return ret
def main():
    print (10 * (3 * GLfloat))
    print (GLfloat * 3 * 10)
    # Note:  Compare return value to vertex index - 1
    # e.g. f 1 2 3 => [0,1,2]
    # f = parse_face_line(['f','1','2','3'])
    # assert(f[0] == 0 and f[1] == 1 and f[2] == 2)

    # f = parse_face_line(['f','1//12','2//8','3//5'])
    # assert(f[0] == 0 and f[1] == 1 and f[2] == 2)

    # f = parse_face_line(['f','1/4/12','2/6/8','3/7/5'])
    # assert(f[0] == 0 and f[1] == 1 and f[2] == 2)

    # f = parse_face_line(['1//12','2//8','3//5'])
    # assert(f==None)

    # v = parse_vertex_line(['v','0.1','0.2','0.3'])
    # assert(v[0] == 0.1 and v[1] == 0.2 and v[2] == 0.3) 

    # v = parse_vertex_line(['v','0.1','0.2','0.3','1','2','3'])
    # assert(v[0] == 0.1 and v[1] == 0.2 and v[2] == 0.3) 

    # v = parse_vertex_line(['v','0.1','0.2'])
    # assert(v == None) 

    # c = obj_line_parsers["#"](["asdasd"])
    # #obj_parse_assignment["#"](c)
    # print(c)

    v,f,uv,n,c = load("cube.obj");
    v,uv = process_obj(v,f,uv,n,c)
    print(v[0])
    print(uv[0])
if __name__ == '__main__':
    main()


