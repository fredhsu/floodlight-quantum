package net.floodlightcontroller.quantumplugin;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

import net.floodlightcontroller.core.IFloodlightProviderService;
import net.floodlightcontroller.core.module.FloodlightModuleContext;
import net.floodlightcontroller.core.module.FloodlightModuleException;
import net.floodlightcontroller.core.module.IFloodlightModule;
import net.floodlightcontroller.core.module.IFloodlightService;
import net.floodlightcontroller.restserver.IRestApiService;
import net.floodlightcontroller.staticflowentry.StaticFlowEntries;

import org.openflow.protocol.OFFlowMod;
import org.openflow.protocol.OFMatch;
import org.openflow.protocol.OFType;
import org.openflow.protocol.factory.BasicFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class QuantumPlugin implements IFloodlightModule {
    protected static Logger log = LoggerFactory.getLogger(QuantumPlugin.class);
	protected IFloodlightProviderService floodlightProvider; //Used to listen for messages
	
    //REST API
    protected IRestApiService restApi;

    private BasicFactory ofMessageFactory;


	@Override
	public Collection<Class<? extends IFloodlightService>> getModuleServices() {
	    Collection<Class<? extends IFloodlightService>> l = new ArrayList<Class<? extends IFloodlightService>>();
	    l.add(QuantumPluginService.class);
	    return l;
	}

	@Override
	public Map<Class<? extends IFloodlightService>, IFloodlightService> getServiceImpls() {
	    Map<Class<? extends IFloodlightService>, IFloodlightService> m = new HashMap<Class<? extends IFloodlightService>, IFloodlightService>();
//	    m.put(QuantumPluginService.class, this);
	    return m;
	}


	@Override
	public Collection<Class<? extends IFloodlightService>> getModuleDependencies() {
		// This module depends on FloodlightProviderService to listen to OF Messages
		Collection<Class<? extends IFloodlightService>> l = new ArrayList<Class<? extends IFloodlightService>>();
		l.add(IFloodlightProviderService.class);
	    l.add(IRestApiService.class);
		return l;
	}

	@Override
	public void init(FloodlightModuleContext context)
			throws FloodlightModuleException {
		floodlightProvider = context.getServiceImpl(IFloodlightProviderService.class);
	    restApi = context.getServiceImpl(IRestApiService.class);
	}

	@Override
	public void startUp(FloodlightModuleContext context) {
		//Want to handle  OF PacketIn messages
	    restApi.addRestletRoutable(new QuantumPluginWebRoutable());
	}
	
	


    /*
     * Need switch dpid, port, uplink port
     * Entryname could be host name?
     * Match on dpid and port
     * Modify with vlan and send to uplink port
     * Need to create two flows, one in and one out
     */
//    @Override
	public void addQuantumFlow(String swDpid, String port, String uplink, Short vlan, String entryName) {
        String actionOutString = "set-vlan-id=" + vlan + ",output=" + uplink;
        String actionInString = "strip-vlan,output=" + port;
		if (ofMessageFactory == null) // lazy init
            ofMessageFactory = new BasicFactory();

        OFFlowMod flowOutMod = (OFFlowMod) ofMessageFactory
                .getMessage(OFType.FLOW_MOD);
        OFFlowMod flowInMod = (OFFlowMod) ofMessageFactory
                .getMessage(OFType.FLOW_MOD);
        StaticFlowEntries.initDefaultFlowMod(flowOutMod, entryName + "Out");
        StaticFlowEntries.initDefaultFlowMod(flowInMod, entryName + "In");
        StaticFlowEntries.parseActionString(flowOutMod, actionOutString, log);
        StaticFlowEntries.parseActionString(flowInMod, actionInString, log);
        //What is the cookie?
        flowOutMod.setCookie(0);
        flowInMod.setCookie(0);
//        flowOutMod.setPriority(PRIORITY_HIGH);
//        flowInMod.setPriority(PRIORITY_HIGH);

        OFMatch matchOut = new OFMatch();
        OFMatch matchIn = new OFMatch();
        matchOut.fromString(OFMatch.STR_IN_PORT + "=" + port);
        matchIn.fromString(OFMatch.STR_DL_VLAN + "=" + vlan);
        flowOutMod.setMatch(matchOut);
        flowInMod.setMatch(matchIn);
        //Use add flow
//        writeFlowModToSwitch(HexString.toLong(swDpid), flowOutMod);
//        writeFlowModToSwitch(HexString.toLong(swDpid), flowInMod);        
	}


}
