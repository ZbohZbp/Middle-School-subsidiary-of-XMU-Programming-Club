# River_distance_measurement.py
# 河流测距 —— 陈思羽

import turtle as t
import math
def circ(d,x,y,r,m=0):
    t.penup()
    t.goto(x,y)
    t.right(90)
    t.fd(d)
    t.left(90)
    t.pendown(90)
    for i in range(0,r,0.01):
        if m:
            t.right(0.01)
        else:
            t.left(0.01)
        t.fd(math.pi*2*d)
    t.penup()
    t.goto(x,y)
while 1:
    CD=int(input("输入基线："))
    a=int(input("alpha:"))
    b=int(input("beta:"))
    y=int(input("gamma:"))
    d=int(input("delta:"))
    AD=math.sin(math.radians(a+b))/math.sin(math.radians(a+b+y))*CD
    AC=math.sin(math.radians(y))/math.sin(math.radians(a+b+y))*CD
    BD=math.sin(math.radians(b))/math.sin(math.radians(a+b+y))*CD
    AB=math.sqrt(AD**2+BD**2-2*AD*BD*math.cos(math.radians(d)))
    t.clear()
    C=(100,200)
    D=(C[0]+CD,C[1])
    A=(C[0]+AC*math.cos(math.radians(a+b)),C[1]+AC*math.sin(math.radians(a+b)))
    B=(D[0]-BD*math.cos(math.radians(y+d)),D[1]+AC*math.sin(math.radians(y+d)))
    t.penup()
    t.goto(*C)
    t.pendown()
    t.write("C")
    t.goto(*D)
    t.write("D")
    t.penup()
    t.goto((C[0]+D[0])/2,(C[1]+D[1])/2)
    t.write(CD)
    t.goto(*D)
    t.pendown()
    t.goto(*B)
    t.write("B")
    t.goto(*A)
    t.write("A")
    t.penup()
    t.goto((A[0]+B[0])/2,(A[1]+B[1])/2)
    t.write(AB)
    t.goto(*A)
    t.pendown()
    t.goto(*C)
    t.goto(*B)
    t.penup()
    t.goto(*A)
    t.pendown()
    t.goto(*D)
