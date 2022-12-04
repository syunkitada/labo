def cmd(cmd, c, spec, rspec):
    if cmd == "dump":
        print(rspec)
    elif cmd == "make":
        make(c, spec, rspec)


def make(c, spec, rspec):
    if c.run("ps ax | grep [m]ysqld", warn=True).failed:
        if c.is_local:
            c.sudo("labo/mysql/mysql.sh")
        else:
            c.put("labo/mysql/mysql.sh", "/tmp/mysql.sh")
            c.sudo("/tmp/mysql.sh")
    return
