def cmd(t):
    if t.cmd == "dump":
        print(t.rspec)
    elif t.cmd == "make":
        make(t.c)


def make(c):
    if c.run("ps ax | grep [m]ysqld", warn=True).failed:
        if c.is_local:
            c.sudo("labo/mysql/mysql.sh")
        else:
            c.put("labo/mysql/mysql.sh", "/tmp/mysql.sh")
            c.sudo("/tmp/mysql.sh")
    return
