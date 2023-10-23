# BELOW IS AN EXAMPLE PRE-INSTALLATION README


# Prepare ActiveMQ Data Collections

This app has been tested with the following ActiveMQ versions:
  * 5.17.4
  * 5.18.2

## For Metrics Collection

  JMX receiver collects activemq metrics (brokers, topics, queues) from ActiveMQ server as part of the OpenTelemetry Collector (OTC).

  1. Follow the instructions in [JMX - OpenTelemetry's prerequisites section](/docs/integrations/app-development/opentelemetry/jmx-opentelemetry/#prerequisites) to download the [JMX Metric Gatherer](https://github.com/open-telemetry/opentelemetry-java-contrib/blob/main/jmx-metrics/README.md) used by the [JMX Receiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/jmxreceiver#details).

  2. Enable reads metrics from ActiveMQ servers via the [JMX MBeans](https://activemq.apache.org/jmx) by setting `useJmx="true"` in file config [ActiveMQ.xml](https://activemq.apache.org/xml-configuration.html)

      ```xml
       <broker useJmx="true" brokerName="BROKER1">
       ...
       </broker>
      ```

  3. Set the JMX port by changing the `ACTIVEMQ_SUNJMX_START` parameter. Usually it is set in `/opt/activemq/bin/env` or `C:\Program Files\apache-activemq\bin\activemq.bat` file.

      ```json
      ACTIVEMQ_SUNJMX_START="$ACTIVEMQ_SUNJMX_START -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=11099 -Dcom.sun.management.jmxremote.ssl=false  -Dcom.sun.management.jmxremote.password.file=${ACTIVEMQ_CONF_DIR}/jmx.password -Dcom.sun.management.jmxremote.access.file=${ACTIVEMQ_CONF_DIR}/jmx.access"
      ```


## For Logs Collection

  1. [Enable auditing](https://activemq.apache.org/audit-logging) if not enabled by default

      `ACTIVEMQ_OPTS="$ACTIVEMQ_OPTS -Dorg.apache.activemq.audit=true"`


  2. Ensure that below log formats are present in [logging configuration](https://activemq.apache.org/how-do-i-change-the-logging). Also make sure appropriate log level is set.

     * [Audit Logs](https://activemq.apache.org/audit-logging):

        `appender.auditlog.layout.pattern=%d | %-5p | %m | %t%n`

     * ActiveMQ Logs:

        `appender.logfile.layout.pattern=%d | %-5p | %m | %c | %t%n%throwable{full}`


  3. By default, ActiveMQ logs (`audit.log` and `activemq.log`) are located in `${ACTIVEMQ_HOME}/data/` directory. Make a note of this location for later use.

     Ensure that the OpenTelemetry Collector has adequate permissions configured. Sumo recommends adding “read” and “execute” permissions for otelcol-sumo.

     Run the following command to add the correct permissions for each folder:

       `sudo setfacl -R -m d:u:otelcol-sumo:r-x,u:otelcol-sumo:r-x,g:otelcol-sumo:r-x <PATH_TO_LOG_FILE>`

     **ACL Support**

       For linux systems with ACL support, the OpenTelemetry Collector install process should have created the ACL grants necessary for the otelcol-sumo system user to access default log locations. You can verify if ACL grants are active using the getfacl command. If ACL is not installed in your Linux environment, please [install it](https://www.xmodulo.com/configure-access-control-lists-acls-linux.html)

       In some [rare cases](https://help.sumologic.com/docs/send-data/sumo-logic-distribution-for-opentelemetry-collector/troubleshooting) required ACL might not be granted (eg. for Linux OS Distributions that Sumo doesn't officially support), in which case you can run the following command to explicitly grant the permissions:

       `sudo setfacl -R -m d:u:otelcol-sumo:r-x,u:otelcol-sumo:r-x,g:otelcol-sumo:r-x <PATH_TO_LOG_FILE>`

       If Linux ACL support isn't available, traditional Unix styled user and group permission must be modified. It should be sufficient to add the otelcol-sumo system user to a specific group which has access to ActiveMQ log files.

ional Unix styled user and group permission must be modified. It should be sufficient to add the otelcol-sumo system user to a specific group which has access to Kafka log files.