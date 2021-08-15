package main

import (
	"fmt"

	do "gopkg.in/godo.v2"
)

func tasks(p *do.Project) {
	p.Task("default", nil, func(c *do.Context) {
		c.Run(fmt.Sprintf("rsync -t -r --delete %s %s",
			"setup-scripts/",
			"/mnt/nfs/setup-scripts/"))
	}).Src("setup-scripts/**/*")
}

func main() {
	do.Godo(tasks)
}

