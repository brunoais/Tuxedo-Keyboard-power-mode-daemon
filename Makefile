
DSTDIR := /usr/local/bin

all: 

update-settings:
	@echo Update settings to to ${DSTDIR}
	@sudo install -m 444 -g adm "power_events.py.run" ${DSTDIR}/

install: update-settings
	@echo Install to ${DSTDIR}
	@pip3 install pidfile==0.1.1
	@sudo install -m 544 -g adm "power_events.py" ${DSTDIR}/
	@sudo install -m 444 -g adm "power_modes.service" "/etc/systemd/system/"
	@sudo systemctl enable "/etc/systemd/system/power_modes.service" --now
