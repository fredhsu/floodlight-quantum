package net.floodlightcontroller.quantumplugin;

import net.floodlightcontroller.staticflowentry.IStaticFlowEntryPusherService;

public interface QuantumPluginService extends IStaticFlowEntryPusherService {
	public void addQuantumFlow(String swDpid, String port, String uplink, Short vlan, String entryName);
}
