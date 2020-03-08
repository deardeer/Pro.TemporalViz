function projectDots(normalVec, centerPos, liDots){
    var a1 = normalVec[0] // vec1[1]*vec2[2] - vec2[1]*vec1[2] // (y1z2-y2z1,
    var b1 = normalVec[1] // vec1[2]*vec2[0] - vec2[2]*vec1[0] // z1x2-z2x1,
    var c1 = normalVec[2] // vec1[0]*vec2[1] - vec2[0]*vec1[1] // x1y2-x2y1)    
    var d1 = -(normalVec[0]*centerPos[0] + normalVec[1]*centerPos[1] + normalVec[2]*centerPos[2])

    var lenABC = a1 * a1 + b1 * b1 + c1 * c1
    var xs = [], ys = [], zs = []
    var liDot_transform = []
    for(var i = 0; i < liDots[0].length; i ++){
        var x_o = liDots[0][i], y_o = liDots[1][i], z_o = liDots[2][i]
        var t = ( a1 * x_o + b1 * y_o + c1 * z_o + d1 ) / lenABC
        var x = x_o - a1 * t;
        var y = y_o - b1 * t;
        var z = z_o - c1 * t;
        liDot_transform.push([x, y, z]);
        xs.push(x)
        ys.push(-y)
        zs.push(z)
    }
    return [liDot_transform, xs, ys, zs]
}

function getZ(a, b, c, point, x, y){
    return point[2] - (a * (x - point[0]) + b * (y - point[1])) / c 
}

function getNormalVector(line1, line2){
    var vec1 = [line1[0][0] - line1[1][0], line1[0][1] - line1[1][1], line1[0][2] - line1[1][2]]
    var vec2 = [line2[0][0] - line2[1][0], line2[0][1] - line2[1][1], line2[0][2] - line2[1][2]]

    // y1z2-y2z1，z1x2-z2x1，x1y2-x2y1

    var a1 = vec1[1]*vec2[2] - vec2[1]*vec1[2] // (y1z2-y2z1,
    var b1 = vec1[2]*vec2[0] - vec2[2]*vec1[0] // z1x2-z2x1,
    var c1 = vec1[0]*vec2[1] - vec2[0]*vec1[1] // x1y2-x2y1)
    return [a1, b1, c1]
}

function getPlane(normalVec, borderX, borderY, centerPos, color){

    // var vec1 = [line1[0][0] - line1[1][0], line1[0][1] - line1[1][1], line1[0][2] - line1[1][2]]
    // var vec2 = [line2[0][0] - line2[1][0], line2[0][1] - line2[1][1], line2[0][2] - line2[1][2]]

    // // y1z2-y2z1，z1x2-z2x1，x1y2-x2y1

    var a1 = normalVec[0] // vec1[1]*vec2[2] - vec2[1]*vec1[2] // (y1z2-y2z1,
    var b1 = normalVec[1] // vec1[2]*vec2[0] - vec2[2]*vec1[0] // z1x2-z2x1,
    var c1 = normalVec[2] // vec1[0]*vec2[1] - vec2[0]*vec1[1] // x1y2-x2y1)        

    var lenABC = Math.sqrt(a1 * a1 + b1 * b1 + c1 * c1)
    var stepBack = 0
    centerPos = [centerPos[0] - stepBack * (a1)/lenABC, centerPos[1] - stepBack * (a1)/lenABC, centerPos[2] - stepBack * (a1)/lenABC]

    // var z_temp = getZ(a1, b1, c1, line1[0], x, y);

    var xStepNum = 6
    var yStepNum = 10
    
    var x1 = []
    var border1 = borderX[0], border2 = borderX[1]

    if(border1 < border2){
        xBegin =  border1
        xStep = (border2 - border1) / (xStepNum - 1);// z1[0].length;
    }else{
        xBegin =  border2
        xStep = (border1 - border2) / (xStepNum - 1); //z1[0].length;
    }

    for(var j = 0; j < xStepNum; j ++){
        tempX = xBegin + xStep * j
        x1.push(tempX);
    }

    var y1 = []
    var border1 = borderY[0], border2 = borderY[1]

    if(border1 < border2){
        xBegin =  border1
        xStep = (border2 - border1) / (yStepNum - 1);
    }else{
        xBegin =  border2
        xStep = (border1 - border2) / (yStepNum - 1);
    }

    console.log('xBegin', xBegin, xStep)

    for(var i = 0; i < yStepNum; i ++){
        tempX = xBegin + xStep * i
        // for(var j = 0; j < z1[i].length; j ++){
        y1.push(tempX);
        // }
    }

    var z1 = []
    var surfaceColor = []
    for(var i = 0; i < yStepNum; i ++){
        var z_row = []
        var row_color = []
        for(var j = 0; j < xStepNum; j ++){
            z_row.push(getZ(a1, b1, c1, centerPos, x1[j], y1[i]))
            row_color.push(0)
        }
        surfaceColor.push(row_color)
        z1.push(z_row)
    }

    console.log('z1', z1, surfaceColor);
    colorscale = [[0, color], [1, color]]

    var data_z1 = {z: z1,
                    type: 'surface', 
                    x: x1, y: y1, 
                    showscale: false,
                    surfacecolor: surfaceColor, 
                    cmin: 0,
                    cmax: 1, 
                    colorscale: colorscale
                                        };
    return data_z1;
}