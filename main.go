package main

import (
	"context"
	"log"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
)

func runCommandInContainer(cli *client.Client, containerName string, command []string) error {
	ctx := context.Background()
	config := &container.Config{
		AttachStdin:  false,
		AttachStdout: true,
		AttachStderr: true,
		Cmd:         command,
		Tty:         false,
	}

	hostConfig := &container.HostConfig{}

	resp, err := cli.ContainerCreate(ctx, config, hostConfig, nil, nil, "")
	if err != nil {
		return err
	}

	if err := cli.ContainerStart(ctx, resp.ID, types.ContainerStartOptions{}); err != nil {
		return err
	}

	return nil
}

func main() {
	// Create a Docker client
	cli, err := client.NewClientWithOpts(client.FromEnv)
	if err != nil {
		log.Fatal(err)
	}

	// Run the loop indefinitely
	for {
		// Run the first command
		err = runCommandInContainer(cli, "skf_mys-django-1", []string{"python", "manage.py", "absentees"})
		if err != nil {
			log.Printf("Error running first command: %v", err)
		}

		// Run the second command
		err = runCommandInContainer(cli, "skf_mys-django-1", []string{"python", "manage.py", "task"})
		if err != nil {
			log.Printf("Error running second command: %v", err)
		}

		// Wait for 1 minute
		time.Sleep(1 * time.Minute)
	}
}