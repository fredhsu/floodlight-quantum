package net.floodlightcontroller.quantumplugin;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import net.floodlightcontroller.staticflowentry.StaticFlowEntries;
import net.floodlightcontroller.staticflowentry.StaticFlowEntryPusher;
import net.floodlightcontroller.storage.IStorageSourceService;

import org.codehaus.jackson.JsonParseException;
import org.codehaus.jackson.map.JsonMappingException;
import org.codehaus.jackson.map.ObjectMapper;
import org.codehaus.jackson.type.TypeReference;
import org.openflow.protocol.factory.BasicFactory;
import org.restlet.resource.Delete;
import org.restlet.resource.Post;
import org.restlet.resource.ServerResource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class QuantumPluginResource extends ServerResource {
    protected static Logger log = LoggerFactory.getLogger(QuantumPluginResource.class);
    private BasicFactory ofMessageFactory;
    public static final String SWITCH_KEY = "switch";
    public static final String VLAN_KEY = "vlan";
    public static final String INGRESS_PORT_KEY = "ingress-port";
    public static final String UPLINK_KEY = "uplink";
    public static final String NAME_KEY = "name";
    public static final String ACTIONS_KEY = "actions";

    @Post
    public void store(String fmJson) {
        IStorageSourceService storageSource =
                (IStorageSourceService)getContext().getAttributes().
                    get(IStorageSourceService.class.getCanonicalName());
        
    	ObjectMapper mapper = new ObjectMapper();
		if (ofMessageFactory == null) // lazy init
            ofMessageFactory = new BasicFactory();

    	try {
    		TypeReference<HashMap<String,Object>> typeRef = new TypeReference<HashMap<String,Object>>() {};
    		Map<String,Object> userData = mapper.readValue(fmJson, typeRef);
			String sw = (String)userData.get(SWITCH_KEY);
			String vlan = (String)userData.get(VLAN_KEY);
			String port = (String)userData.get(INGRESS_PORT_KEY);
			String uplink = (String)userData.get(UPLINK_KEY);
			String name = (String)userData.get(NAME_KEY);

			//Used JSON objects to create flows, tried using FlowMod objects but it inserts lots of default values
			//Outbound flow tagged with VLAN
			Map<String,Object> outData = new HashMap<String,Object>();
			outData.put(SWITCH_KEY, sw);
			outData.put(NAME_KEY, name + "out");
			outData.put(INGRESS_PORT_KEY, port);
			outData.put(ACTIONS_KEY, "set-vlan-id=" + vlan + ",output=" + uplink);
			String outJson = mapper.writeValueAsString(outData);
            Map<String, Object> outValues = StaticFlowEntries.jsonToStorageEntry(outJson); 			
			storageSource.insertRowAsync(StaticFlowEntryPusher.TABLE_NAME, outValues);

			//Inbound flow strips VLAN
			Map<String,Object> inData = new HashMap<String,Object>();
			inData.put(SWITCH_KEY, sw);
			inData.put(NAME_KEY, name + "in");
			inData.put(VLAN_KEY, vlan);
			inData.put(ACTIONS_KEY, "strip-vlan,output=" + port);
			String inJson = mapper.writeValueAsString(inData);			
            Map<String, Object> inValues = StaticFlowEntries.jsonToStorageEntry(inJson);
			storageSource.insertRowAsync(StaticFlowEntryPusher.TABLE_NAME, inValues);
		} catch (JsonParseException e) {
			e.printStackTrace();
		} catch (JsonMappingException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}    	
    }
    
    @Delete
    public void del(String fmJson) {
        IStorageSourceService storageSource =
                (IStorageSourceService)getContext().getAttributes().
                    get(IStorageSourceService.class.getCanonicalName());        
        try {
            String fmName = StaticFlowEntries.getEntryNameFromJson(fmJson);
            storageSource.deleteRow(StaticFlowEntryPusher.TABLE_NAME, fmName);
        } catch (IOException e) {
            log.error("Error deleting flow mod request: " + fmJson, e);
            e.printStackTrace();
        }
    }
}
