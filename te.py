class t:
    def __init__(self,a,b,c):
        self.a=a
        self.b=b
        self.c=c
    def plot(self):
        print(self.a)
        print(self.b)
        print(self.c)

context={
    'a':1,
    'b':20,
    'c':3
}

a=t(**context)
a.plot()