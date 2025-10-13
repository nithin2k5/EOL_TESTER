using Microsoft.VisualBasic.ApplicationServices;
using Modbus.Device;
using System;
using System.Collections.Generic;
using System.Configuration;
using System.Data;
using System.Data.OleDb;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Ports;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace EOLTester
{
    public partial class TestConsole : Form
    {
        private Stopwatch sw = new Stopwatch();
        private Int32 alcInput_TimeInterval = 3000; // 200 for barcode scanner and 3000 for manual entry
        private Int32 printedLabelScanDataInput_TimeInterval = 4000; // 4000 for barcode scanner data
        private Int32 printedLabelScanDataInput_WaitTime = 6000; // 6 secs wait for receiving printed label scan data
        private Int32 alertOn_TimeInterval = 5000; // 5 secs wait until the alert stops
        private bool printedLabelScanDataInput_Received = false;
        private string barcodePrintFileName = string.Empty;
        private string barcodePrintFileNamePath = string.Empty;
        private string prnFileContent =string.Empty;
        private string partNumber = string.Empty;
        private string modelName = string.Empty;
        private string vendorCode = string.Empty;
        private string eoNumber = string.Empty;
        private string specialData = string.Empty;
        private string initialID = string.Empty;
        private string supplierSection = string.Empty;
        private DataTable mldDataTable = new DataTable();
        private string lotNo = string.Empty;
        private string traceabilityCode = string.Empty;
        private DateTime today = DateTime.Today;
        private int dataPointX = 0;

        private string machineID = string.Empty;
        private bool startingNGCableValidation = false;
        private bool endingNGCableValidated = false;
        private bool endingNGCableValidation = false;
        private List<string> deviceToRead = new List<string>();

        private string loadcell01Data;
        private string loadcell02Data;
        private string loadcell03Data;
        private string loadcell04Data;

        private double loadcell01Value = 0.0;
        private double loadcell02Value = 0.0;
        private double loadcell03Value = 0.0;
        private double loadcell04Value = 0.0;

        private double L1MaxValue = 0.0;
        private double L2MaxValue = 0.0;
        private double L3MaxValue = 0.0;
        private double L4MaxValue = 0.0;

        private string lvdtData;
        private int noOfValues = 0;
        private double P01Value = 0.0;
        private double P02Value = 0.0;
        private double P03Value = 0.0;
        private double P04Value = 0.0;

        private bool breakLoop = false;
        private bool keepWriting = true;
        private int failCounter = 0;
        private int passCounter = 0;
        private bool blink;

        private bool columnL2 = false;
        private bool columnL3 = false;
        private bool columnL4 = false;
        private bool columnP3 = false;
        private bool columnP4 = false;

        ModbusSerialMaster _modbusMaster;
        private int slaveAddress;
        private string[] inputSensorsArray;
        private string[] processStatusArray;
        private string[] employeeCodesArray;
        private string[] processStatusLabels = { "AUTO", "HOME", "PULL1_OK", "PULL1_NG", "PULL2_OK", "PULL2_NG", "TESTRESULT_OK", "TESTRESULT_NG" };
        private bool rcvdTestRslt = false;
        private List<string> inputSensorsToReadList = new List<string>();
        private string programSelectionPLCAddress = string.Empty;

        private string cam1Result = string.Empty;

        private bool resetPLCOnFormClosing = false;

        private string machineOnPLCCoilAddress = string.Empty;
        private string alertOnPLCCoilAddress = string.Empty;
        private bool partRunningSerialExists = false;

        public TestConsole()
        {
            InitializeComponent();
            getAddresses();
            statusStrip1.Padding = new Padding(statusStrip1.Padding.Left, statusStrip1.Padding.Top, statusStrip1.Padding.Left, statusStrip1.Padding.Bottom);
        }

        public void getAddresses()
        {
            string inputSensors = File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "InputSensors.txt"));
            if (inputSensors.Length > 0)
                inputSensorsArray = inputSensors.Split(',');
            else
                MessageBox.Show("Input Sensors text file is either missing or empty!!");

            string processStatus = File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "ProcessStatus.txt"));
            if (processStatus.Length > 0)
                processStatusArray = processStatus.Split(',');
            else
                MessageBox.Show("Process Status addresses text file is either missing or empty!!");
        }

        private void TestConsole_Load(object sender, EventArgs e)
        {
            if (Common.Utils.getPixels(10M) == 0)
            {
                MessageBox.Show("Monitor/Screen Size is NOT set. Please go to COMPort Settings Form and update Screen Size.");
                this.Close();
                return;
            }

            var configSettings = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
            var settings = configSettings.AppSettings.Settings;

            if (settings["MACHINE_ID"] != null)
            {
                lbl_MacID.Text = settings["MACHINE_ID"].Value;
                machineID = settings["MACHINE_ID"].Value;
            }

            machineOnPLCCoilAddress = File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "MachineOnPLCCoilAddress.txt"));
            alertOnPLCCoilAddress = File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "AlertOnPLCCoilAddress.txt"));

            this.ActiveControl = txt_EmpCode;
            txt_EmpCode.ReadOnly = false;
            openCOMPorts();
        }

        private void openCOMPorts()
        {
            bool comPortSettings = true;

            var configSettings = ConfigurationManager.OpenExeConfiguration(ConfigurationUserLevel.None);
            var settings = configSettings.AppSettings.Settings;

            if (settings["COMPORT_LVDT"] != null && settings["BAUDRATE_LVDT"] != null && settings["COMPORT_LVDT"].Value != string.Empty && settings["BAUDRATE_LVDT"].Value != string.Empty)
            {
                if (serialPort_LVDT.IsOpen) serialPort_LVDT.Close();
                OpenPort(serialPort_LVDT, settings["COMPORT_LVDT"].Value, settings["BAUDRATE_LVDT"].Value);
            }
            else
                comPortSettings = false;

            if (settings["COMPORT_PLC"] != null && settings["BAUDRATE_PLC"] != null && settings["STATION_ID_PLC"] != null && settings["COMPORT_PLC"].Value != string.Empty && settings["BAUDRATE_PLC"].Value != string.Empty && settings["STATION_ID_PLC"].Value != string.Empty)
            {
                Int32.TryParse(settings["STATION_ID_PLC"].Value, out slaveAddress);
                if (serialPort_PLC.IsOpen)
                {
                    _modbusMaster.Dispose();
                    _modbusMaster = null;

                    ClosePort(serialPort_PLC);
                }
                OpenPort(serialPort_PLC, settings["COMPORT_PLC"].Value, settings["BAUDRATE_PLC"].Value);

                _modbusMaster = ModbusSerialMaster.CreateRtu(serialPort_PLC);
                _modbusMaster.Transport.ReadTimeout = 500;
                _modbusMaster.Transport.WriteTimeout = 500;
                _modbusMaster.Transport.Retries = 0;
            }
            else
                comPortSettings = false;

            if (settings["COMPORT_LOADCELL_01"] != null && settings["BAUDRATE_LOADCELL_01"] != null && settings["COMPORT_LOADCELL_01"].Value != string.Empty && settings["BAUDRATE_LOADCELL_01"].Value != string.Empty)
            {
                if (serialPort_L1.IsOpen) serialPort_L1.Close();
                OpenPort(serialPort_L1, settings["COMPORT_LOADCELL_01"].Value, settings["BAUDRATE_LOADCELL_01"].Value);
            }
            else
                comPortSettings = false;

            if (settings["COMPORT_LOADCELL_02"] != null && settings["BAUDRATE_LOADCELL_02"] != null && settings["COMPORT_LOADCELL_02"].Value != string.Empty && settings["BAUDRATE_LOADCELL_02"].Value != string.Empty)
            {
                if (serialPort_L2.IsOpen) serialPort_L2.Close();
                OpenPort(serialPort_L2, settings["COMPORT_LOADCELL_02"].Value, settings["BAUDRATE_LOADCELL_02"].Value);
            }

            if (settings["COMPORT_LOADCELL_03"] != null && settings["BAUDRATE_LOADCELL_03"] != null && settings["COMPORT_LOADCELL_03"].Value != string.Empty && settings["BAUDRATE_LOADCELL_03"].Value != string.Empty)
            {
                if (serialPort_L3.IsOpen) serialPort_L3.Close();
                OpenPort(serialPort_L3, settings["COMPORT_LOADCELL_03"].Value, settings["BAUDRATE_LOADCELL_03"].Value);
            }

            if (settings["COMPORT_LOADCELL_04"] != null && settings["BAUDRATE_LOADCELL_04"] != null && settings["COMPORT_LOADCELL_04"].Value != string.Empty && settings["BAUDRATE_LOADCELL_04"].Value != string.Empty)
            {
                if (serialPort_L4.IsOpen) serialPort_L4.Close();
                OpenPort(serialPort_L4, settings["COMPORT_LOADCELL_04"].Value, settings["BAUDRATE_LOADCELL_04"].Value);
            }

            if (!comPortSettings)
            {
                MessageBox.Show("Please check COM Port Settings page...");
            }
        }

        private void OpenPort(SerialPort serialPort, string port, string baudrate)
        {
            // Open Port...
            serialPort.PortName = port;
            serialPort.BaudRate = int.Parse(baudrate);
            serialPort.Parity = Parity.None;
            serialPort.StopBits = StopBits.One;
            serialPort.DataBits = 8;
            serialPort.Open();
            serialPort.ReadTimeout = SerialPort.InfiniteTimeout;
            serialPort.WriteTimeout = 1000;
        }

        private void resizePictureBoxImage(PictureBox pictureBox)
        {
            var imageSize = pictureBox.Image.Size;
            var fitSize = pictureBox.ClientSize;
            pictureBox.SizeMode = imageSize.Width > fitSize.Width || imageSize.Height > fitSize.Height ? PictureBoxSizeMode.Zoom : PictureBoxSizeMode.CenterImage;
        }

        private void txt_EmpCode_KeyPress(object sender, KeyPressEventArgs e)
        {
            if (e.KeyChar == Convert.ToChar(Keys.Enter))
            {
                string employeeCodes = File.ReadAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "EmployeeCodes.txt"));
                if (employeeCodes.Length > 0)
                {
                    employeeCodesArray = employeeCodes.Split(',');

                    if (employeeCodesArray.Contains<string>(txt_EmpCode.Text))
                    {
                        txt_ALC.ReadOnly = false;
                        txt_EmpCode.ReadOnly = true;
                        this.ActiveControl = txt_ALC;
                    }
                    else
                    {
                        MessageBox.Show("Employee code: " + txt_EmpCode.Text + " is NOT AUTHORIZED to operate this machine, please consult SUPERVISOR.");
                        txt_EmpCode.Text = string.Empty;
                        this.ActiveControl = txt_EmpCode;
                    }
                }
                else
                {
                    MessageBox.Show("Employee Codes text file is either missing or empty!!");
                }
                e.Handled = true; 
            }
        }

        private async void txt_ALC_TextChanged(object sender, EventArgs e)
        {
            if (txt_ALC.Text.Length == 1)
            {
                sw.Start();
                do
                {
                    await Task.Delay(10);
                } while (sw.ElapsedMilliseconds < alcInput_TimeInterval);
                txt_ALC.ReadOnly = true;
                sw.Reset();

                bool partExists = false;
                barcodePrintFileName = string.Empty;
                prnFileContent = string.Empty;

                //using (OleDbConnection dbCon = new OleDbConnection(Properties.Settings.Default.DBConnectionString))
                using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
                using (var cmd = dbCon.CreateCommand())
                {
                    cmd.CommandText = "SELECT * FROM TBL_MODEL_MASTER WHERE MM_ALC_CODE = @alcCode AND MM_STATUS = @isActive";
                    cmd.Parameters.AddWithValue("alcCode", txt_ALC.Text);
                    cmd.Parameters.AddWithValue("isActive", true);
                    dbCon.Open();
                    var reader = cmd.ExecuteReader();
                    while (reader.Read())
                    {
                        partNumber = reader["MM_PART_NUMBER"].ToString().ToUpper();
                        modelName = reader["MM_MODEL_NAME"].ToString().ToUpper();
                        vendorCode = reader["MM_VENDOR_CODE"].ToString().ToUpper();
                        eoNumber = reader["MM_EO_NUMBER"].ToString().ToUpper();
                        specialData = reader["MM_SPECIAL_DATA"].ToString().ToUpper();
                        initialID = reader["MM_INITIAL_ID"].ToString().ToUpper();
                        supplierSection = reader["MM_SUPPLIER_SECTION"].ToString().ToUpper();
                        lbl_PartNameAndNumber.Text = modelName + " - " + partNumber;
                        string imagePath = reader["MM_IMAGE_PATH"].ToString();
                        if (imagePath.Length > 0)
                        {
                            pictureBox_PartImage.Image = Image.FromFile(imagePath);
                            resizePictureBoxImage(pictureBox_PartImage);
                        }
                        barcodePrintFileName = reader["MM_BARCODE_PRN_FILE_NAME"].ToString();
                        if (!string.IsNullOrWhiteSpace(barcodePrintFileName) && !(barcodePrintFileName == "NO_BARCODE_PRINT_FILE"))
                        {
                            barcodePrintFileNamePath = AppDomain.CurrentDomain.BaseDirectory + barcodePrintFileName;
                            Path.GetInvalidPathChars().ToList().ForEach(c => barcodePrintFileNamePath = barcodePrintFileNamePath.Replace(c.ToString(), ""));
                            prnFileContent = File.ReadAllText(barcodePrintFileNamePath);
                        }

                        programSelectionPLCAddress = reader["MM_PLC_ADDRESS"].ToString().Substring(1);
                        ushort writePLCCoilAddress = (ushort)Convert.ToUInt32(programSelectionPLCAddress, 16);
                        _modbusMaster.WriteSingleCoil((byte)slaveAddress, writePLCCoilAddress, true);

                        // Writing to PLC for Machine On function
                        if (machineOnPLCCoilAddress.Length > 0)
                        {
                            ushort writeMachineOnPLCCoilAddress = (ushort)Convert.ToUInt32(machineOnPLCCoilAddress.Substring(1), 16);
                            _modbusMaster.WriteSingleCoil((byte)slaveAddress, writeMachineOnPLCCoilAddress, true);
                        }
                        else
                        {
                            MessageBox.Show("Machine On PLC Coil Address text file is either missing or empty!!");
                        }

                        partExists = true;
                    }
                }

                if (partExists)
                {
                    //using (OleDbConnection dbCon = new OleDbConnection(Properties.Settings.Default.DBConnectionString))
                    using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
                    {
                        dbCon.Open();
                        OleDbDataAdapter adapter = new OleDbDataAdapter(" SELECT MS_DESCRIPTION, MS_DEVICE, MS_NORMAL_MIN, MS_UNIT, MS_NORMAL_MAX FROM TBL_MODEL_SPECIFICATION WHERE MS_PART_NUMBER = '" + partNumber + "' ORDER BY MS_DEVICE ", dbCon);
                        DataTable dataTable = new DataTable();
                        adapter.Fill(dataTable);

                        dGV_Spec.AutoGenerateColumns = false;
                        dGV_Spec.DataSource = dataTable;
                        dGV_Spec.ClearSelection();
                    }

                    foreach (DataGridViewRow row in dGV_Spec.Rows)
                    {
                        if (dGV_Spec.Rows.Count <= 4)
                            row.Height = 72;
                        else
                            row.Height = 36;

                        string val = row.Cells["MS_DEVICE"].Value.ToString().ToUpper();
                        deviceToRead.Add(val);
                        if (val.Equals("L2"))
                        {
                            dGV_Data.Columns["L02"].Visible = true;
                            columnL2 = true;
                        }
                        else if (val.Equals("L3"))
                        {
                            dGV_Data.Columns["L03"].Visible = true;
                            columnL3 = true;
                        }
                        else if (val.Equals("L4"))
                        {
                            dGV_Data.Columns["L04"].Visible = true;
                            columnL4 = true;
                        }
                        else if (val.Equals("P3"))
                        {
                            dGV_Data.Columns["P3"].Visible = true;
                            columnP3 = true;
                        }
                        else if (val.Equals("P4"))
                        {
                            dGV_Data.Columns["P4"].Visible = true;
                            columnP4 = true;
                        }
                    }

                    //using (OleDbConnection dbCon = new OleDbConnection(Properties.Settings.Default.DBConnectionString))
                    using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
                    {
                        dbCon.Open();
                        OleDbDataAdapter adapter = new OleDbDataAdapter(" SELECT MLD_LABEL_ID, MLD_ON_STATUS, MLD_OFF_STATUS, MLD_X, MLD_Y, MLD_FONT FROM TBL_MODEL_LABEL_DETAILS WHERE MLD_PART_NUMBER = '" + partNumber + "' ", dbCon);
                        adapter.Fill(mldDataTable);

                        foreach (DataRow row in mldDataTable.Rows)
                        {
                            if (row.Field<string>("MLD_ON_STATUS").Trim() != string.Empty)
                            {
                                inputSensorsToReadList.Add(row.Field<string>("MLD_LABEL_ID"));
                                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().Visible = true;
                                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().Text = row.Field<string>("MLD_OFF_STATUS");
                                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().ForeColor = Color.OrangeRed;
                                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().Font = new FontConverter().ConvertFromString(row.Field<String>("MLD_FONT")) as Font;
                                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().Location = new Point(row.Field<int>("MLD_X"), row.Field<int>("MLD_Y"));
                            }
                        }
                    }

                    display_Data();
                    load_Graph();
                    getLotNumber();

                    messageLabel.Text = "Please Validate NG Cable...";
                    messageLabel.ForeColor = Color.Black;
                    startingNGCableValidation = true;
                    start_CheckAsync();
                }
                else
                {
                    MessageBox.Show("Scanned Part Does NOT Exist...");
                    txt_ALC.Text = string.Empty;
                    txt_ALC.ReadOnly = false;
                    txt_ALC.Focus();
                }
            }
        }

        private async void ReadSensorInputs()
        {
            ushort sensorAddress;
            int index;
            bool result;

            do
            {
                foreach (string inputSensor in inputSensorsToReadList)
                {
                    index = Convert.ToInt16(inputSensor.Substring(1));
                    sensorAddress = (ushort)Convert.ToUInt32(inputSensorsArray[index].Substring(1), 16);
                    result = (_modbusMaster.ReadInputs((byte)slaveAddress, sensorAddress, 1))[0];

                    if (result)
                    {
                        this.Controls.Find(inputSensor, true).FirstOrDefault().Text = mldDataTable.Rows[index].Field<string>("MLD_ON_STATUS");
                        this.Controls.Find(inputSensor, true).FirstOrDefault().ForeColor = Color.Blue;
                    }
                    else
                    {
                        this.Controls.Find(inputSensor, true).FirstOrDefault().Text = mldDataTable.Rows[index].Field<string>("MLD_OFF_STATUS");
                        this.Controls.Find(inputSensor, true).FirstOrDefault().ForeColor = Color.OrangeRed;
                    }
                }
                await Task.Delay(200);
            } while (!rcvdTestRslt);
        }

        private async void ReadCoils()
        {
            rcvdTestRslt = false;

            ushort autoAddress = (ushort)Convert.ToUInt32(processStatusArray[0].Substring(1), 16);
            ushort homeAddress = (ushort)Convert.ToUInt32(processStatusArray[1].Substring(1), 16);
            ushort pull1OKAddress = (ushort)Convert.ToUInt32(processStatusArray[2].Substring(1), 16);
            ushort pull1NGAddress = (ushort)Convert.ToUInt32(processStatusArray[3].Substring(1), 16);
            ushort pull2OKAddress = (ushort)Convert.ToUInt32(processStatusArray[4].Substring(1), 16);
            ushort pull2NGAddress = (ushort)Convert.ToUInt32(processStatusArray[5].Substring(1), 16);
            ushort testResultOKAddress = (ushort)Convert.ToUInt32(processStatusArray[6].Substring(1), 16);
            ushort testResultNGAddress = (ushort)Convert.ToUInt32(processStatusArray[7].Substring(1), 16);
            ushort cam1OKAddress = (ushort)Convert.ToUInt32(processStatusArray[8].Substring(1), 16);
            ushort cam1NGAddress = (ushort)Convert.ToUInt32(processStatusArray[9].Substring(1), 16);
            ushort cam1ONOFFAddress = (ushort)Convert.ToUInt32(processStatusArray[10].Substring(1), 16);

            do
            {
                bool autoResult = (_modbusMaster.ReadCoils((byte)slaveAddress, autoAddress, 1))[0];
                bool homeResult = (_modbusMaster.ReadCoils((byte)slaveAddress, homeAddress, 1))[0];
                bool pull1OKResult = (_modbusMaster.ReadCoils((byte)slaveAddress, pull1OKAddress, 1))[0];
                bool pull1NGResult = (_modbusMaster.ReadCoils((byte)slaveAddress, pull1NGAddress, 1))[0];
                bool pull2OKResult = (_modbusMaster.ReadCoils((byte)slaveAddress, pull2OKAddress, 1))[0];
                bool pull2NGResult = (_modbusMaster.ReadCoils((byte)slaveAddress, pull2NGAddress, 1))[0];
                bool testResultOKResult = (_modbusMaster.ReadCoils((byte)slaveAddress, testResultOKAddress, 1))[0];
                bool testResultNGResult = (_modbusMaster.ReadCoils((byte)slaveAddress, testResultNGAddress, 1))[0];
                bool cam1OKResult = (_modbusMaster.ReadCoils((byte)slaveAddress, cam1OKAddress, 1))[0];
                bool cam1NGResult = (_modbusMaster.ReadCoils((byte)slaveAddress, cam1NGAddress, 1))[0];
                bool cam1ONOFFResult = (_modbusMaster.ReadCoils((byte)slaveAddress, cam1ONOFFAddress, 1))[0];

                if (autoResult)
                    Controls.Find(processStatusLabels[0], true).FirstOrDefault().BackColor = Color.Lime;
                else
                    Controls.Find(processStatusLabels[0], true).FirstOrDefault().BackColor = Color.DeepSkyBlue;

                if (homeResult)
                    Controls.Find(processStatusLabels[1], true).FirstOrDefault().BackColor = Color.Lime;
                else
                    Controls.Find(processStatusLabels[1], true).FirstOrDefault().BackColor = Color.DeepSkyBlue;

                if (pull1OKResult)
                    Controls.Find(processStatusLabels[2].Substring(0, processStatusLabels[2].IndexOf('_')), true).FirstOrDefault().BackColor = Color.Lime;
                else if (pull1NGResult)
                    Controls.Find(processStatusLabels[2].Substring(0, processStatusLabels[2].IndexOf('_')), true).FirstOrDefault().BackColor = Color.OrangeRed;
                else if (!pull1OKResult && !pull1NGResult)
                    Controls.Find(processStatusLabels[2].Substring(0, processStatusLabels[2].IndexOf('_')), true).FirstOrDefault().BackColor = Color.DeepSkyBlue;

                if (pull2OKResult)
                    Controls.Find(processStatusLabels[4].Substring(0, processStatusLabels[4].IndexOf('_')), true).FirstOrDefault().BackColor = Color.Lime;
                else if (pull2NGResult)
                    Controls.Find(processStatusLabels[4].Substring(0, processStatusLabels[4].IndexOf('_')), true).FirstOrDefault().BackColor = Color.OrangeRed;
                else if (!pull2OKResult && !pull2NGResult)
                    Controls.Find(processStatusLabels[4].Substring(0, processStatusLabels[4].IndexOf('_')), true).FirstOrDefault().BackColor = Color.DeepSkyBlue;

                if (testResultOKResult)
                    Controls.Find(processStatusLabels[6].Substring(0, processStatusLabels[6].IndexOf('_')), true).FirstOrDefault().BackColor = Color.Lime;
                else if (testResultNGResult)
                    Controls.Find(processStatusLabels[6].Substring(0, processStatusLabels[6].IndexOf('_')), true).FirstOrDefault().BackColor = Color.OrangeRed;
                else if (!testResultOKResult && !testResultNGResult)
                    Controls.Find(processStatusLabels[6].Substring(0, processStatusLabels[6].IndexOf('_')), true).FirstOrDefault().BackColor = Color.DeepSkyBlue;

                if (cam1ONOFFResult)
                {
                    if (cam1OKResult && cam1NGResult)
                    {
                        CAM1STATUS.Text = "CAMERA ONE ERROR";
                        CAM1STATUS.BackColor = Color.Orange;
                    }
                    else if (!cam1OKResult && !cam1NGResult)
                    {
                        CAM1STATUS.Text = "CAMERA ONE ON";
                        CAM1STATUS.BackColor = Color.DeepSkyBlue;
                    }
                    else
                    {
                        if (cam1OKResult)
                        {
                            CAM1STATUS.BackColor = Color.Lime;
                            CAM1STATUS.Text = "CAMERA ONE PASS";
                            cam1Result = "PASS";
                        }
                        else if (cam1NGResult)
                        {
                            CAM1STATUS.BackColor = Color.Red;
                            CAM1STATUS.Text = "CAMERA ONE NG";
                        }
                    }
                }
                else
                {
                    CAM1STATUS.Text = "CAMERA ONE OFF";
                    cam1Result = "OFF";
                }

                if (testResultOKResult) rcvdTestRslt = true;
                else if (testResultNGResult) rcvdTestRslt = true;

                await Task.Delay(200);

            } while (!rcvdTestRslt);
        }

        private async void start_CheckAsync()
        {
            ReadCoils();
            ReadSensorInputs();
            do
            {
                await Task.Delay(50);

                if (keepWriting)
                {
                    serialPort_L1.Write("ID01P");
                    if (columnL2) serialPort_L2.Write("ID01P");
                    if (columnL3) serialPort_L3.Write("ID01P");
                    if (columnL4) serialPort_L4.Write("ID01P");
                }

                if (breakLoop)
                {
                    break;
                }

            } while (noOfValues == 0);

            if (!breakLoop)
            {
                foreach (DataGridViewRow row in dGV_Spec.Rows)
                {
                    if (row.Cells["MS_DEVICE"].Value.ToString().Equals("L1"))
                    {
                        row.Cells["ACTUAL"].Value = L1MaxValue;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > L1MaxValue || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < L1MaxValue)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                    else if (row.Cells["MS_DEVICE"].Value.ToString().Equals("L2"))
                    {
                        row.Cells["ACTUAL"].Value = L2MaxValue;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > L2MaxValue || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < L2MaxValue)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                    else if (row.Cells["MS_DEVICE"].Value.ToString().Equals("L3"))
                    {
                        row.Cells["ACTUAL"].Value = L3MaxValue;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > L3MaxValue || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < L3MaxValue)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                    else if (row.Cells["MS_DEVICE"].Value.ToString().Equals("L4"))
                    {
                        row.Cells["ACTUAL"].Value = L4MaxValue;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > L4MaxValue || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < L4MaxValue)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                    else if (row.Cells["MS_DEVICE"].Value.ToString().Equals("P1"))
                    {
                        row.Cells["ACTUAL"].Value = P01Value;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > P01Value || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < P01Value)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                    else if (row.Cells["MS_DEVICE"].Value.ToString().Equals("P2"))
                    {
                        row.Cells["ACTUAL"].Value = P02Value;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > P02Value || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < P02Value)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                    else if (row.Cells["MS_DEVICE"].Value.ToString().Equals("P3"))
                    {
                        row.Cells["ACTUAL"].Value = P03Value;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > P03Value || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < P03Value)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                    else if (row.Cells["MS_DEVICE"].Value.ToString().Equals("P4"))
                    {
                        row.Cells["ACTUAL"].Value = P04Value;
                        if (double.Parse(row.Cells["MS_NORMAL_MIN"].Value.ToString()) > P04Value || double.Parse(row.Cells["MS_NORMAL_MAX"].Value.ToString()) < P04Value)
                        {
                            row.Cells["RESULT"].Value = "NG";
                            row.Cells["RESULT"].Style.ForeColor = Color.OrangeRed;
                            failCounter++;
                        }
                        else
                        {
                            row.Cells["RESULT"].Value = "PASS";
                            row.Cells["RESULT"].Style.ForeColor = Color.Blue;
                            passCounter++;
                        }
                    }
                }

                if (startingNGCableValidation)
                {
                    if (failCounter > 0)
                    {
                        messageLabel.Text = "NG Validation successful, continue to testing...";
                        startingNGCableValidation = false;
                    }
                    else
                    {
                        messageLabel.Text = "NG Validation NOT OK, please repeat NG Validation...";
                    }
                }
                else if (endingNGCableValidation)
                {
                    if (failCounter > 0)
                    {
                        messageLabel.Text = "NG Validation successful.";
                        endingNGCableValidated = true;
                        endingNGCableValidation = false;

                        ushort writePLCCoilAddress = (ushort)Convert.ToUInt32(programSelectionPLCAddress, 16);
                        _modbusMaster.WriteSingleCoil((byte)slaveAddress, writePLCCoilAddress, false);
                    }
                    else
                    {
                        messageLabel.Text = "NG Validation NOT OK, please repeat NG Validation...";
                        endingNGCableValidated = false;
                    }
                }
                else
                {
                    if ((DateTime.Today - today).TotalDays >= 1)
                    {
                        lotNo = "0";
                        today = DateTime.Today;
                        partRunningSerialExists = false;
                    }

                    int j = Convert.ToInt32(lotNo);
                    j += 1;
                    lotNo = j.ToString("D7");
                    traceabilityCode = DateTime.Now.ToString("yyMMdd") + "I" + machineID.Substring(2) + "G1A" + lotNo;

                    bool traceabilityCodeExists = false;
                    //barcodePrintFileName = string.Empty;

                    using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
                    {
                        dbCon.Open();
                        OleDbDataAdapter adapter = new OleDbDataAdapter("SELECT TD_TRACEABILITY_CODE FROM TBL_TEST_DATA WHERE TD_PART_NUMBER = '" + partNumber + "' AND TD_RECORD_DATE = #" + DateTime.Today.ToShortDateString() + "# AND TD_TRACEABILITY_CODE = '" + traceabilityCode + "'", dbCon);
                        DataTable dataTable = new DataTable();
                        adapter.Fill(dataTable);

                        if (dataTable.Rows.Count >= 1)
                            traceabilityCodeExists = true;
                    }

                    if ((passCounter == dGV_Spec.Rows.Count) && !traceabilityCodeExists)
                    {
                        save_Testing_Data("OK");
                        if (!string.IsNullOrWhiteSpace(barcodePrintFileName) && !(barcodePrintFileName == "NO_BARCODE_PRINT_FILE"))
                        {
                            txt_PrintedLabelScanData.ReadOnly = false;
                            txt_PrintedLabelScanData.Focus();
                            printBarcodeLabelAsync();
                        }
                    }
                    else
                    {
                        if (traceabilityCodeExists)
                        {
                            MessageBox.Show("Generated Traceability Code: " + traceabilityCode + " for Part Number: " + partNumber + " already exists among today's records in the Database. The current test result will be saved as 'NG'.");
                        }
                        save_Testing_Data("NG");
                    }

                    if (loadChart.Series["L1"].Points.Count >= 1000)
                    {
                        loadChart.Series["L1"].Points.RemoveAt(0);
                        if (columnL2) loadChart.Series["L2"].Points.RemoveAt(0);
                        if (columnL3) loadChart.Series["L3"].Points.RemoveAt(0);
                        if (columnL4) loadChart.Series["L4"].Points.RemoveAt(0);

                        lengthChart.Series["P1"].Points.RemoveAt(0);
                        lengthChart.Series["P2"].Points.RemoveAt(0);
                        if (columnP3) lengthChart.Series["P3"].Points.RemoveAt(0);
                        if (columnP4) lengthChart.Series["P4"].Points.RemoveAt(0);
                    }

                    loadChart.Series["L1"].Points.AddXY(dataPointX, L1MaxValue);
                    if (columnL2) loadChart.Series["L2"].Points.AddXY(dataPointX, L2MaxValue);
                    if (columnL3) loadChart.Series["L3"].Points.AddXY(dataPointX, L3MaxValue);
                    if (columnL4) loadChart.Series["L4"].Points.AddXY(dataPointX, L4MaxValue);

                    lengthChart.Series["P1"].Points.AddXY(dataPointX, P01Value);
                    lengthChart.Series["P2"].Points.AddXY(dataPointX, P02Value);
                    if (columnP3) lengthChart.Series["P3"].Points.AddXY(dataPointX, P03Value);
                    if (columnP4) lengthChart.Series["P4"].Points.AddXY(dataPointX, P04Value);

                    lengthChart.ResetAutoValues();
                    loadChart.ResetAutoValues();

                    dataPointX++;
                }
                await Task.Delay(1200);
                resetTestParameters();
                resetDGVSpecData();

                // Writing to PLC for Machine On function
                if (machineOnPLCCoilAddress.Length > 0)
                {
                    //MessageBox.Show("machineOnPLCCoilAddress " + machineOnPLCCoilAddress);
                    ushort writeMachineOnPLCCoilAddress = (ushort)Convert.ToUInt32(machineOnPLCCoilAddress.Substring(1), 16);
                    //MessageBox.Show("writeMachineOnPLCCoilAddress " + writeMachineOnPLCCoilAddress);
                    _modbusMaster.WriteSingleCoil((byte)slaveAddress, writeMachineOnPLCCoilAddress, true);
                    //MessageBox.Show("After Writing to PLC");
                }
                else
                {
                    MessageBox.Show("Machine On PLC Coil Address text file is either missing or empty!!");
                }

                if (!endingNGCableValidated)
                    start_CheckAsync();
                else
                    refreshFormForNextPart();
            }
            else
            {
                breakLoop = false;
            }
        }

        private void save_Testing_Data(string status)
        {
            //using (OleDbConnection dbCon = new OleDbConnection(Properties.Settings.Default.DBConnectionString))
            using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
            using (var cmd = dbCon.CreateCommand())
            {
                cmd.CommandText = "INSERT INTO TBL_TEST_DATA (TD_MACHINE_ID, TD_PART_NUMBER, TD_LOT_NUMBER, TD_TRACEABILITY_CODE, TD_RECORD_DATE, TD_DATETIME, L1";

                if (columnL2)
                    cmd.CommandText += ", L2";
                if (columnL3)
                    cmd.CommandText += ", L3";
                if (columnL4)
                    cmd.CommandText += ", L4";

                cmd.CommandText += ", P1, P2";

                if (columnP3)
                    cmd.CommandText += ", P3";
                if (columnP4)
                    cmd.CommandText += ", P4";

                cmd.CommandText += ", CAM1, TD_OVERALL_STATUS, TD_EMPLOYEE_CODE) " +
                    " VALUES (@macId, @partnumber, @lotId, @traceabilityCode, @recordDate, @date, @L1";

                if (columnL2)
                    cmd.CommandText += ", @L2";
                if (columnL3)
                    cmd.CommandText += ", @L3";
                if (columnL4)
                    cmd.CommandText += ", @L4";

                cmd.CommandText += ", @P1, @P2";

                if (columnP3)
                    cmd.CommandText += ", @P3";
                if (columnP4)
                    cmd.CommandText += ", @P4";

                cmd.CommandText += ", @cam1Result, @status, @empCode) ";

                cmd.Parameters.AddWithValue("macId", machineID);
                cmd.Parameters.AddWithValue("partnumber", partNumber);
                cmd.Parameters.AddWithValue("lotId", lotNo);
                cmd.Parameters.AddWithValue("traceabilityCode", traceabilityCode);
                cmd.Parameters.AddWithValue("recordDate", GetDateAlone(DateTime.Now));
                cmd.Parameters.AddWithValue("date", GetDateWithoutMilliseconds(DateTime.Now));
                cmd.Parameters.AddWithValue("L1", L1MaxValue);
                if (columnL2)
                    cmd.Parameters.AddWithValue("L2", L2MaxValue);
                if (columnL3)
                    cmd.Parameters.AddWithValue("L3", L3MaxValue);
                if (columnL4)
                    cmd.Parameters.AddWithValue("L4", L4MaxValue);
                cmd.Parameters.AddWithValue("P1", P01Value);
                cmd.Parameters.AddWithValue("P2", P02Value);
                if (columnP3)
                    cmd.Parameters.AddWithValue("P3", P03Value);
                if (columnP4)
                    cmd.Parameters.AddWithValue("P4", P04Value);
                cmd.Parameters.AddWithValue("cam1Result", cam1Result);
                cmd.Parameters.AddWithValue("status", status);
                cmd.Parameters.AddWithValue("empCode", txt_EmpCode.Text);
                dbCon.Open();
                cmd.ExecuteNonQuery();
            }

            // Code to Insert/Update Part Running Serial Table
            if (status.Equals("OK"))
            {
                if (!partRunningSerialExists)
                {
                    using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
                    using (var cmd = dbCon.CreateCommand())
                    {
                        cmd.CommandText = " INSERT INTO TBL_PART_RUNNING_SERIAL (PART_NUMBER, TEST_DAY_DATE, TEST_DAY_LAST_DATE_TIME, TRACEABILITY_CODE, RUNNING_LOT_NUMBER) " +
                            " VALUES (@partNumber, @date, @lastDateTime, @traceabilityCode, @lotId) ";
                        cmd.Parameters.AddWithValue("partNumber", partNumber);
                        cmd.Parameters.AddWithValue("date", GetDateAlone(DateTime.Now));
                        cmd.Parameters.AddWithValue("lastDateTime", GetDateWithoutMilliseconds(DateTime.Now));
                        cmd.Parameters.AddWithValue("traceabilityCode", traceabilityCode);
                        cmd.Parameters.AddWithValue("lotId", lotNo);

                        dbCon.Open();
                        cmd.ExecuteNonQuery();
                    }
                    partRunningSerialExists = true;
                }
                else
                {
                    using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
                    using (var cmd = dbCon.CreateCommand())
                    {
                        cmd.CommandText = " UPDATE TBL_PART_RUNNING_SERIAL SET TEST_DAY_LAST_DATE_TIME = @lastDateTime, TRACEABILITY_CODE = @traceabilityCode, " +
                            " RUNNING_LOT_NUMBER = @lotId WHERE PART_NUMBER = @partNumber AND TEST_DAY_DATE = #" + DateTime.Today.ToShortDateString() + "# ";
                        cmd.Parameters.AddWithValue("lastDateTime", GetDateWithoutMilliseconds(DateTime.Now));
                        cmd.Parameters.AddWithValue("traceabilityCode", traceabilityCode);
                        cmd.Parameters.AddWithValue("lotId", lotNo);
                        cmd.Parameters.AddWithValue("partNumber", partNumber);

                        dbCon.Open();
                        cmd.ExecuteNonQuery();
                    }
                }
            }

            display_Data();
        }

        private DateTime GetDateWithoutMilliseconds(DateTime d)
        {
            return new DateTime(d.Year, d.Month, d.Day, d.Hour, d.Minute, d.Second);
        }

        private DateTime GetDateAlone(DateTime d)
        {
            return new DateTime(d.Year, d.Month, d.Day);
        }

        private void resetDGVSpecData()
        {
            foreach (DataGridViewRow row in dGV_Spec.Rows)
            {
                row.Cells["ACTUAL"].Value = string.Empty;
                row.Cells["RESULT"].Value = string.Empty;
                row.Cells["RESULT"].Style.ForeColor = Color.Black;
            }
        }

        private void resetTestParameters()
        {
            messageLabel.Text = string.Empty;
            messageLabel.ForeColor = Color.Black;

            AUTO.BackColor = Color.DeepSkyBlue;
            HOME.BackColor = Color.DeepSkyBlue;
            PULL1.BackColor = Color.DeepSkyBlue;
            PULL2.BackColor = Color.DeepSkyBlue;
            TESTRESULT.BackColor = Color.DeepSkyBlue;

            CAM1STATUS.BackColor = Color.DeepSkyBlue;
            CAM1STATUS.Text = "CAMERA ONE STATUS";

            loadcell01Value = 0.0;
            loadcell02Value = 0.0;
            loadcell03Value = 0.0;
            loadcell04Value = 0.0;

            L1MaxValue = 0.0;
            L2MaxValue = 0.0;
            L3MaxValue = 0.0;
            L4MaxValue = 0.0;

            P01Value = 0.0;
            P02Value = 0.0;
            P03Value = 0.0;
            P04Value = 0.0;

            noOfValues = 0;
            failCounter = 0;
            passCounter = 0;

            rcvdTestRslt = false;
            cam1Result = string.Empty;
        }

        private void refreshFormForNextPart()
        {
            inputSensorsToReadList.Clear();
            endingNGCableValidated = false;
            partRunningSerialExists = false;

            dGV_Data.DataSource = null;
            resetScanResultCounters();
            dGV_Spec.DataSource = null;
            pictureBox_PartImage.Image = null;
            lbl_PartNameAndNumber.Text = string.Empty;

            foreach (DataRow row in mldDataTable.Rows)
            {
                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().Visible = false;
                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().Text = row.Field<string>("MLD_LABEL_ID");
                this.Controls.Find(row.Field<string>("MLD_LABEL_ID"), true).FirstOrDefault().ForeColor = Color.Black;
            }
            mldDataTable.Clear();

            loadChart.Series["L1"].Points.Clear();
            loadChart.Series["L2"].Points.Clear();
            loadChart.Series["L3"].Points.Clear();
            loadChart.Series["L4"].Points.Clear();
            lengthChart.Series["P1"].Points.Clear();
            lengthChart.Series["P2"].Points.Clear();
            lengthChart.Series["P3"].Points.Clear();
            lengthChart.Series["P4"].Points.Clear();
            dataPointX = 0;

            btn_NextModel.Enabled = true;
            txt_ALC.Text = string.Empty;
            txt_EmpCode.Text = string.Empty;
            txt_EmpCode.ReadOnly = false;
            txt_EmpCode.Focus();
        }

        private void messageLabel_TextChanged(object sender, EventArgs e)
        {
            blink = false;
            if (messageLabel.Text.Length > 0)
                BlinkStatus();
        }

        private async void BlinkStatus()
        {
            string status = messageLabel.Text;
            blink = true;
            do
            {
                messageLabel.Visible = false;
                await Task.Delay(600);
                messageLabel.Visible = true;
                await Task.Delay(800);
            } while (blink);
        }

        private void display_Data()
        {
            dGV_Data.DataSource = null;

            if (columnL2)
                dGV_Data.Columns["L02"].Visible = true;
            if (columnL3)
                dGV_Data.Columns["L03"].Visible = true;
            if (columnL4)
                dGV_Data.Columns["L04"].Visible = true;
            if (columnP3)
                dGV_Data.Columns["P3"].Visible = true;
            if (columnP4)
                dGV_Data.Columns["P4"].Visible = true;

            //using (OleDbConnection dbCon = new OleDbConnection(Properties.Settings.Default.DBConnectionString))
            using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
            {
                dbCon.Open();
                OleDbDataAdapter adapter = new OleDbDataAdapter("SELECT * FROM TBL_TEST_DATA WHERE TD_RECORD_DATE >= #" + DateTime.Today.ToShortDateString() + "# AND TD_RECORD_DATE <= #" + DateTime.Today.ToShortDateString() + "# AND TD_PART_NUMBER = '" + partNumber + "' AND TD_OVERALL_STATUS = 'OK' ORDER BY ID DESC", dbCon);
                DataTable dataTable = new DataTable();
                adapter.Fill(dataTable);

                updateScanResultCounters(dataTable);

                dGV_Data.AutoGenerateColumns = false;
                dGV_Data.DataSource = dataTable;
                int k = 1;
                for (int j = dGV_Data.Rows.Count - 1; j >= 0; j--)
                {
                    if (k >= 1 & k <= 5)
                        dGV_Data.Rows[j].DefaultCellStyle.BackColor = Color.FromArgb(255, 255, 153);
                    else
                        dGV_Data.Rows[j].DefaultCellStyle.BackColor = Color.White;
                    k++;
                    if (k == 11)
                        k = 1;
                }
                dGV_Data.ClearSelection();
            }

            dGV_Data.Refresh();
        }

        private void load_Graph()
        {
            //using (OleDbConnection dbCon = new OleDbConnection(Properties.Settings.Default.DBConnectionString))
            using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
            {
                dbCon.Open();
                OleDbCommand command = new OleDbCommand("SELECT COUNT(*) FROM TBL_TEST_DATA WHERE TD_PART_NUMBER = '" + partNumber + "' AND TD_RECORD_DATE >= #" + DateTime.Today.ToShortDateString() + "# AND TD_RECORD_DATE <= #" + DateTime.Today.ToShortDateString() + "#", dbCon);
                int noOfRecords = (int)command.ExecuteScalar();

                OleDbDataAdapter adapter = new OleDbDataAdapter("SELECT TOP 1000 ID, L1, L2, L3, L4, P1, P2, P3, P4 FROM TBL_TEST_DATA WHERE TD_PART_NUMBER = '" + partNumber + "' AND TD_RECORD_DATE >= #" + DateTime.Today.ToShortDateString() + "# AND TD_RECORD_DATE <= #" + DateTime.Today.ToShortDateString() + "# ORDER BY ID DESC", dbCon);
                DataTable dataTable = new DataTable();
                adapter.Fill(dataTable);
                dataTable = resort(dataTable, "ID", "ASC");

                int i = (noOfRecords > 1000) ? noOfRecords - 1000 : 0;
                foreach (DataRow row in dataTable.Rows)
                {
                    i++;

                    loadChart.Series["L1"].Points.AddXY(i, double.Parse(row.Field<string>("L1")));
                    if (columnL2) loadChart.Series["L2"].Points.AddXY(i, double.Parse(row.Field<string>("L2")));
                    if (columnL3) loadChart.Series["L3"].Points.AddXY(i, double.Parse(row.Field<string>("L3")));
                    if (columnL4) loadChart.Series["L4"].Points.AddXY(i, double.Parse(row.Field<string>("L4")));

                    lengthChart.Series["P1"].Points.AddXY(i, double.Parse(row.Field<string>("P1")));
                    lengthChart.Series["P2"].Points.AddXY(i, double.Parse(row.Field<string>("P2")));
                    if (columnP3) lengthChart.Series["P3"].Points.AddXY(i, double.Parse(row.Field<string>("P3")));
                    if (columnP4) lengthChart.Series["P4"].Points.AddXY(i, double.Parse(row.Field<string>("P4")));
                }
                dataPointX = i + 1;
            }
        }

        public static DataTable resort(DataTable dt, string colName, string direction)
        {
            dt.DefaultView.Sort = colName + " " + direction;
            return dt.DefaultView.ToTable();
        }

        private void getLotNumber()
        {
            using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
            {
                string lotNumFromDB = string.Empty;
                dbCon.Open();
                OleDbDataAdapter adapter = new OleDbDataAdapter("SELECT TOP 1 RUNNING_LOT_NUMBER FROM TBL_PART_RUNNING_SERIAL WHERE PART_NUMBER = '" + partNumber + "' AND TEST_DAY_DATE = #" + DateTime.Today.ToShortDateString() + "# ORDER BY RUNNING_LOT_NUMBER DESC", dbCon);
                DataTable dataTable = new DataTable();
                adapter.Fill(dataTable);

                foreach (DataRow row in dataTable.Rows)
                {
                    lotNumFromDB = row.Field<string>("RUNNING_LOT_NUMBER");
                    break;
                }
                lotNo = (!string.IsNullOrEmpty(lotNumFromDB) ? lotNumFromDB : "0");
                if (!string.IsNullOrEmpty(lotNumFromDB)) partRunningSerialExists = true;
            }
        }

        private void btn_NextModel_Click(object sender, EventArgs e)
        {
            if (MessageBox.Show("Do you really want to move on to a different part?", "Confirm Move", MessageBoxButtons.YesNo) == DialogResult.Yes)
            {
                breakLoop = true;
                btn_NextModel.Enabled = false;
                messageLabel.Text = "Please Validate NG Cable...";
                messageLabel.ForeColor = Color.Black;
                endingNGCableValidation = true;
                resetDGVSpecData();
                resetTestParameters();
                start_CheckAsync();
            }
        }

        private async void printBarcodeLabelAsync()
        {
            string printFileText = prnFileContent;

            printFileText = printFileText.Replace("@alcCode@", txt_ALC.Text);
            printFileText = printFileText.Replace("@partNumber@", partNumber);
            printFileText = printFileText.Replace("@modelName@", modelName);
            printFileText = printFileText.Replace("@vendorCode@", vendorCode);
            printFileText = printFileText.Replace("@eoNumber@", eoNumber);
            printFileText = printFileText.Replace("@specialData@", specialData);
            printFileText = printFileText.Replace("@initialID@", initialID);
            printFileText = printFileText.Replace("@supplierSection@", supplierSection);
            printFileText = printFileText.Replace("@lotNo@", lotNo);
            printFileText = printFileText.Replace("@traceabilityCode@", traceabilityCode);
            printFileText = printFileText.Replace("@L1MaxValue@", String.Format("{0:0.0}", L1MaxValue));
            printFileText = printFileText.Replace("@L2MaxValue@", String.Format("{0:0.0}", L2MaxValue));
            printFileText = printFileText.Replace("@L3MaxValue@", String.Format("{0:0.0}", L3MaxValue));
            printFileText = printFileText.Replace("@L4MaxValue@", String.Format("{0:0.0}", L4MaxValue));
            if (P01Value < 0)
                printFileText = printFileText.Replace("@P01Value@", String.Format("{0:0.00}", P01Value));
            else
                printFileText = printFileText.Replace("@P01Value@", "+"+String.Format("{0:0.00}", P01Value));
            if (P02Value < 0)
                printFileText = printFileText.Replace("@P02Value@", String.Format("{0:0.00}", P02Value));
            else
                printFileText = printFileText.Replace("@P02Value@", "+" + String.Format("{0:0.00}", P02Value));
            if (P03Value < 0)
                printFileText = printFileText.Replace("@P03Value@", String.Format("{0:0.00}", P03Value));
            else
                printFileText = printFileText.Replace("@P03Value@", "+" + String.Format("{0:0.00}", P03Value));
            if (P03Value < 0)
                printFileText = printFileText.Replace("@P04Value@", String.Format("{0:0.00}", P04Value));
            else
                printFileText = printFileText.Replace("@P04Value@", "+" + String.Format("{0:0.00}", P04Value));
            printFileText = printFileText.Replace("@ddMMyy@", GetDateTime(DateTime.Now, "ddMMyy"));
            printFileText = printFileText.Replace("@HH:mm:ss@", GetDateTime(DateTime.Now, "HH:mm:ss"));
            printFileText = printFileText.Replace("@machineID@", machineID);
            printFileText = printFileText.Replace("@machineID_NoAlphabet@", machineID.Substring(2));

            string tmpFileName = Path.Combine(Path.GetTempPath(), $"EOL_LABEL_{Guid.NewGuid()}.prn");

            try
            {
                File.WriteAllText(tmpFileName, printFileText);
                await Task.Delay(200); // Optional delay to ensure the file system settles
                Common.RawPrinterHelper.SendFileToPrinter(Common.Constants.printerName, tmpFileName);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Printing failed: {ex.Message}", "Print Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                // Clean up the temporary file
                if (File.Exists(tmpFileName))
                {
                    try
                    {
                        File.Delete(tmpFileName);
                    }
                    catch
                    {
                        // Swallow exceptions silently or log if needed
                    }
                }
            }
            sw.Start();
            do
            {
                await Task.Delay(10);
            } while (sw.ElapsedMilliseconds < printedLabelScanDataInput_WaitTime && !printedLabelScanDataInput_Received);
            sw.Reset();

            // Scanner could not detect any barcode...Update scan result as '***'
            if (!printedLabelScanDataInput_Received)
            {
                UpdateScanResult("***");
                txt_PrintedLabelScanData.ReadOnly = true;
                display_Data();
            }
        }

        private void UpdateScanResult(string rslt)
        {
            using (OleDbConnection dbCon = new OleDbConnection(Common.Constants.dbConnectionString))
            using (var cmd = dbCon.CreateCommand())
            {
                cmd.CommandText = " UPDATE TBL_TEST_DATA SET TD_BARCODE_SCAN_RESULT = @result " +
                    " WHERE TD_PART_NUMBER = @partNumber AND TD_TRACEABILITY_CODE = @traceabilityCode ";
                cmd.Parameters.AddWithValue("result", rslt);
                cmd.Parameters.AddWithValue("partNumber", partNumber);
                cmd.Parameters.AddWithValue("traceabilityCode", traceabilityCode);

                dbCon.Open();
                cmd.ExecuteNonQuery();
            }
        }

        private string GetDateTime(DateTime d, string format)
        {
            return (d.ToString(format));
        }

        private void serialPort_L1_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            loadcell01Data = serialPort_L1.ReadLine();
            this.BeginInvoke(new EventHandler(UpdateL1MaxValue));
        }

        private void UpdateL1MaxValue(object sender, EventArgs e)
        {
            string[] tokens = loadcell01Data.Split(',');
            if (tokens.Length == 2)
            {
                double.TryParse(tokens[1], out loadcell01Value);
                if (loadcell01Value > L1MaxValue)
                    L1MaxValue = loadcell01Value;
            }
        }

        private void serialPort_L2_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            loadcell02Data = serialPort_L2.ReadLine();
            this.BeginInvoke(new EventHandler(UpdateL2MaxValue));
        }

        private void UpdateL2MaxValue(object sender, EventArgs e)
        {
            string[] tokens = loadcell02Data.Split(',');
            if (tokens.Length == 2)
            {
                double.TryParse(tokens[1], out loadcell02Value);
                if (loadcell02Value > L2MaxValue)
                    L2MaxValue = loadcell02Value;
            }
        }

        private void serialPort_L3_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            loadcell03Data = serialPort_L3.ReadLine();
            this.BeginInvoke(new EventHandler(UpdateL3MaxValue));
        }

        private void UpdateL3MaxValue(object sender, EventArgs e)
        {
            string[] tokens = loadcell03Data.Split(',');
            if (tokens.Length == 2)
            {
                double.TryParse(tokens[1], out loadcell03Value);
                if (loadcell03Value > L3MaxValue)
                    L3MaxValue = loadcell03Value;
            }
        }

        private void serialPort_L4_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            loadcell04Data = serialPort_L4.ReadLine();
            this.BeginInvoke(new EventHandler(UpdateL4MaxValue));
        }

        private void UpdateL4MaxValue(object sender, EventArgs e)
        {
            string[] tokens = loadcell04Data.Split(',');
            if (tokens.Length == 2)
            {
                double.TryParse(tokens[1], out loadcell04Value);
                if (loadcell04Value > L4MaxValue)
                    L4MaxValue = loadcell04Value;
            }
        }

        private void serialPort_LVDT_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            lvdtData = serialPort_LVDT.ReadLine();
            this.BeginInvoke(new EventHandler(UpdateLVDTValues));
        }

        private void UpdateLVDTValues(object sender, EventArgs e)
        {
            if (lvdtData.Length > 0)
            {
                string[] tokens = lvdtData.Split(',');
                if (tokens.Length > 1)
                {
                    if (int.Parse(tokens[1]) == 2)
                    {
                        double.TryParse(tokens[2], out P01Value);
                        double.TryParse(tokens[3].Substring(0, 5), out P02Value);
                        P01Value = P01Value / 100;
                        P02Value = P02Value / 100;
                        noOfValues = 2;
                    }
                    else if (int.Parse(tokens[1]) == 4)
                    {
                        double.TryParse(tokens[2], out P01Value);
                        double.TryParse(tokens[3], out P02Value);
                        double.TryParse(tokens[4], out P03Value);
                        double.TryParse(tokens[5].Substring(0, 5), out P04Value);
                        P01Value = P01Value / 100;
                        P02Value = P02Value / 100;
                        P03Value = P03Value / 100;
                        P04Value = P04Value / 100;
                        noOfValues = 4;
                    }
                }
            }
        }

        private void dGV_Spec_CellFormatting(object sender, DataGridViewCellFormattingEventArgs e)
        {
            if (e.ColumnIndex == 0)
                if (e.Value != null)
                {
                    e.Value = e.Value.ToString().ToUpper();
                    e.FormattingApplied = true;
                }
        }

        private void TestConsole_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (!resetPLCOnFormClosing)
            {
                if (!string.IsNullOrWhiteSpace(programSelectionPLCAddress))
                {
                    resetPLCOnFormClosing = true;
                    ushort writePLCCoilAddress = (ushort)Convert.ToUInt32(programSelectionPLCAddress, 16);
                    _modbusMaster.WriteSingleCoil((byte)slaveAddress, writePLCCoilAddress, false);
                }
            }

            rcvdTestRslt = true;
            breakLoop = true;
            keepWriting = false;

            if (serialPort_LVDT.IsOpen || serialPort_L1.IsOpen || serialPort_L2.IsOpen || serialPort_L3.IsOpen || serialPort_L4.IsOpen || serialPort_Cam1.IsOpen || serialPort_Cam2.IsOpen)
            {
                e.Cancel = true; //cancel the fom closing
                Thread CloseDown = new Thread(new ThreadStart(CloseSerialPortsOnExit)); //close port in new thread to avoid hang
                CloseDown.Start(); //close port in new thread to avoid hang
            }
        }

        private void CloseSerialPortsOnExit()
        {
            try
            {
                if (serialPort_LVDT.IsOpen)
                {
                    serialPort_LVDT.DataReceived -= serialPort_LVDT_DataReceived;
                    serialPort_LVDT.Close();
                }

                if (serialPort_PLC.IsOpen)
                {
                    serialPort_PLC.Close();
                }

                if (serialPort_L1.IsOpen)
                {
                    serialPort_L1.DataReceived -= serialPort_L1_DataReceived;
                    serialPort_L1.Close();
                }

                if (serialPort_L2.IsOpen)
                {
                    serialPort_L2.DataReceived -= serialPort_L2_DataReceived;
                    serialPort_L2.Close();
                }

                if (serialPort_L3.IsOpen)
                {
                    serialPort_L3.DataReceived -= serialPort_L3_DataReceived;
                    serialPort_L3.Close();
                }

                if (serialPort_L4.IsOpen)
                {
                    serialPort_L4.DataReceived -= serialPort_L4_DataReceived;
                    serialPort_L4.Close();
                }

                if (serialPort_Cam1.IsOpen)
                {
                    serialPort_Cam1.Close();
                }

                if (serialPort_Cam2.IsOpen)
                {
                    serialPort_Cam2.Close();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Serial Port Closing Error: " + ex.StackTrace); //catch any serial port closing error messages
            }
            this.BeginInvoke(new EventHandler(NowClose)); //now close back in the main thread
        }

        private void NowClose(object sender, EventArgs e)
        {
            this.Close(); //now close the form
        }

        private void ClosePort(SerialPort serialPort)
        {
            serialPort.DiscardInBuffer();
            serialPort.Close();
        }

        private async void txt_PrintedLabelScanData_TextChangedAsync(object sender, EventArgs e)
        {
            // Trigger only on first character typed
            if (txt_PrintedLabelScanData.Text.Length != 1 || txt_PrintedLabelScanData.ReadOnly)
                return;

            // Make textbox readonly to prevent re-entry
            txt_PrintedLabelScanData.ReadOnly = true;

            // Wait for scanner to finish input
            await Task.Delay(printedLabelScanDataInput_TimeInterval);

            string scannedText = txt_PrintedLabelScanData.Text;

            printedLabelScanDataInput_Received = true;

            if (scannedText.Contains(traceabilityCode))
            {
                UpdateScanResult("OK");
            }
            else
            {
                UpdateScanResult("NG");

                if (!string.IsNullOrWhiteSpace(alertOnPLCCoilAddress))
                {
                    ushort coilAddress = Convert.ToUInt16(alertOnPLCCoilAddress.Substring(1), 16);

                    _modbusMaster.WriteSingleCoil((byte)slaveAddress, coilAddress, true);

                    // Start timer in background to turn alert off
                    _ = Task.Run(async () =>
                    {
                        await Task.Delay(alertOn_TimeInterval);
                        _modbusMaster.WriteSingleCoil((byte)slaveAddress, coilAddress, false);
                    });

                    MessageBox.Show(
                        "Barcode Scan found NG.\nDo NOT fix the Barcode Label to the part.\nPaste it on Production Log Book as NG.",
                        "Scan NG",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    );
                }
                else
                {
                    MessageBox.Show("Alert On PLC Coil Address text file is either missing or empty!!", "PLC Alert Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }

            txt_PrintedLabelScanData.Text = string.Empty;
            txt_PrintedLabelScanData.ReadOnly = false;
            display_Data();
            printedLabelScanDataInput_Received = false;
        }

        private void updateScanResultCounters(DataTable dt)
        {
            okCountLabel.Text = dt.AsEnumerable().Where(c => c["TD_BARCODE_SCAN_RESULT"].ToString() == "OK").ToList().Count.ToString();
            ngCountLabel.Text = dt.AsEnumerable().Where(c => c["TD_BARCODE_SCAN_RESULT"].ToString() == "NG").ToList().Count.ToString();
            invalidCountLabel.Text = dt.AsEnumerable().Where(c => c["TD_BARCODE_SCAN_RESULT"].ToString() == "***").ToList().Count.ToString();
            totalCountLabel.Text = dt.Rows.Count.ToString();
        }

        private void resetScanResultCounters()
        {
            okCountLabel.Text = string.Empty;
            ngCountLabel.Text = string.Empty;
            invalidCountLabel.Text = string.Empty;
            totalCountLabel.Text = string.Empty;
        }
    }
}


